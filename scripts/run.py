#!/usr/bin/env python3
"""
Run checks and a real agent interaction against the OpenClaw gateway:
1. WebSocket + HTTP health checks
2. POST /v1/responses (OpenResponses API) to run one agent query — no device identity needed.
Exits 0 if the gateway is reachable and the agent responds.
"""

import asyncio
import json
import os
import sys


def _ws_url_to_http(ws_url: str) -> str:
    """Convert ws://host:port or wss://host:port to http(s)://host:port."""
    if ws_url.startswith("wss://"):
        return "https://" + ws_url[6:]
    if ws_url.startswith("ws://"):
        return "http://" + ws_url[5:]
    return ws_url


async def check_websocket(url: str, timeout: float) -> tuple[bool, str]:
    """Connect via WebSocket and wait for connect.challenge. Return (ok, message)."""
    from websockets.asyncio.client import connect as ws_connect

    async with ws_connect(url, open_timeout=timeout) as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=timeout)
        data = json.loads(msg)
        event = data.get("event") or data.get("type") or ""
        if "connect" in event.lower() or "challenge" in event.lower():
            return True, "WebSocket connect.challenge received"
        return False, f"Unexpected message event: {event!r}"


async def check_health(http_base: str, timeout: float) -> tuple[bool, str]:
    """GET /healthz (or /readyz) and return (ok, message)."""
    try:
        import httpx
    except ImportError:
        return False, "httpx not available (poetry install)"

    for path in ("/healthz", "/readyz"):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.get(f"{http_base.rstrip('/')}{path}")
                if r.status_code == 200:
                    return True, f"HTTP {path} -> {r.status_code}"
                return False, f"HTTP {path} -> {r.status_code}"
        except Exception as e:
            continue
    return False, f"Health endpoints unreachable: {e}"


async def run_agent_interaction(
    http_base: str, token: str, timeout: float
) -> tuple[bool, str]:
    """
    Call the gateway HTTP /v1/responses API (no WebSocket device handshake).
    Requires gateway.http.endpoints.responses.enabled in config.
    """
    try:
        import httpx
    except ImportError:
        return False, "httpx not available (poetry install)"

    prompt = os.environ.get("OPENCLAW_RUN_PROMPT", "Reply with exactly: OK Carnitas")
    agent_id = os.environ.get("OPENCLAW_AGENT_ID", "main")
    url = f"{http_base.rstrip('/')}/v1/responses"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "x-openclaw-agent-id": agent_id,
                },
                json={"model": "openclaw", "input": prompt},
            )
        if r.status_code != 200:
            try:
                body = r.json()
                err = body.get("error", {})
                if isinstance(err, dict):
                    err = err.get("message", err.get("code", str(body)))
                else:
                    err = str(err)
            except Exception:
                err = r.text or str(r.status_code)
            hint = ""
            if r.status_code == 500:
                hint = " (gateway may be missing Google credentials: set GOOGLE_APPLICATION_CREDENTIALS_JSON in .env; see README)"
            return False, f"HTTP {r.status_code}: {err}{hint}"

        data = r.json()
        # OpenResponses: output is array of items; message items have content: [{ type: "text", text: "..." }]
        output = data.get("output") or []
        text_parts = []
        for item in output if isinstance(output, list) else []:
            if not isinstance(item, dict):
                continue
            content = item.get("content") or item.get("text")
            if isinstance(content, list):
                for c in content:
                    if isinstance(c, dict) and "text" in c:
                        text_parts.append(c["text"])
            elif content:
                text_parts.append(str(content))
        reply = " ".join(text_parts).strip() if text_parts else "(no text in response)"
        return True, f"Agent replied: {reply!r}"
    except httpx.TimeoutException:
        return False, "Agent request timed out"
    except Exception as e:
        return False, str(e).strip()


async def main() -> int:
    ws_url = os.environ.get("OPENCLAW_GATEWAY_WS_URL", "ws://127.0.0.1:18789")
    timeout = float(os.environ.get("OPENCLAW_TEST_TIMEOUT", "10"))
    agent_timeout = float(os.environ.get("OPENCLAW_AGENT_TIMEOUT", "60"))
    http_base = _ws_url_to_http(ws_url)

    results: list[str] = []

    # 1. WebSocket check
    try:
        ok, msg = await check_websocket(ws_url, timeout)
        if ok:
            results.append(f"WebSocket: {msg}")
        else:
            print(f"WebSocket: {msg}", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"WebSocket error: {e}", file=sys.stderr)
        print("Ensure the OpenClaw service is running (e.g. npm run start).", file=sys.stderr)
        return 1

    # 2. HTTP health check
    ok, msg = await check_health(http_base, timeout)
    if ok:
        results.append(f"Health: {msg}")
    else:
        results.append(f"Health: {msg} (non-fatal)")

    # 3. Real agent interaction (HTTP /v1/responses — no device identity needed)
    token = os.environ.get("OPENCLAW_GATEWAY_TOKEN", "")
    if not token:
        print("Agent: OPENCLAW_GATEWAY_TOKEN not set; skipping agent call.", file=sys.stderr)
        return 1
    ok, msg = await run_agent_interaction(http_base, token, agent_timeout)
    if ok:
        results.append(f"Agent: {msg}")
    else:
        print(f"Agent: {msg}", file=sys.stderr)
        return 1

    print("OpenClaw gateway checks:")
    for r in results:
        print(f"  ✓ {r}")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
