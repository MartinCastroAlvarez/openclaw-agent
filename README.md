# openclaw-agent

A **Python** project that uses the [OpenClaw](https://openclaw.ai) SDK to talk to a local OpenClaw gateway. It includes a minimal client, tests, and npm scripts to run the gateway (Docker) and run tests against it.

## What is OpenClaw?

OpenClaw is a framework for running autonomous AI agents that can use messaging channels (e.g. WhatsApp, Telegram). This repo uses the official **Python SDK** ([openclaw-sdk](https://pypi.org/project/openclaw-sdk/)) to connect to a running OpenClaw gateway over WebSocket (`ws://127.0.0.1:18789/gateway`).

## Requirements

- **Python 3.11+**
- **Poetry** — Python dependency and environment management ([install Poetry](https://python-poetry.org/docs/#installation))
- **Docker** (and Docker Compose) — to run the OpenClaw gateway for `npm run start`
- **npm** (or Node) — only for the `package.json` scripts; no Node app code

## Development setup (Python)

Install dependencies and the package with Poetry (creates/uses a virtual env automatically):

```bash
poetry install
```

Then `npm run test` runs via `poetry run`, so no need to activate the venv yourself.

### 1. Start the OpenClaw gateway (needed for tests)

```bash
npm run start
```

This starts the OpenClaw gateway in Docker on port **18789** (foreground). Stop it with **Ctrl+C**.

The gateway and the SDK use a shared token for auth. By default both use `dev-token-local-only`. To use your own token, set `OPENCLAW_GATEWAY_TOKEN` (e.g. in a `.env` file or `export OPENCLAW_GATEWAY_TOKEN=your-token`) before running `npm run start` and `npm run test`.

**LLM provider (Gemini via Vertex):** The gateway uses **Google Vertex** (`google-vertex/gemini-2.0-flash`) with Application Default Credentials. Put your service account JSON in **`config/google-credentials.json`** (this file is gitignored). The container mounts it and sets `GOOGLE_APPLICATION_CREDENTIALS`; the entrypoint creates `auth-profiles.json` for the google-vertex provider on first run. If you see "No API key found for provider google-vertex", reset the volume and restart: `npm run stop` then `docker compose down -v` then `npm run start`.

### 2. Run the OpenClaw test

```bash
npm run test
```

This runs `poetry install` (if needed) and `scripts/run.py`, which (1) checks **WebSocket** and **HTTP health**, then (2) runs a **real agent interaction** via the gateway HTTP API (`POST /v1/responses`). The script sends one prompt (default: "Reply with exactly: OK Carnitas") with your token; no device pairing is required. Set `OPENCLAW_RUN_PROMPT`, `OPENCLAW_AGENT_TIMEOUT` (seconds), and `OPENCLAW_AGENT_ID` to customize. The gateway config enables `gateway.http.endpoints.responses`. Restart the gateway after changing config (`npm run stop` then `npm run start`).

**Expected output** when the gateway is running and credentials are configured:

```
OpenClaw gateway checks:
  ✓ WebSocket: WebSocket connect.challenge received
  ✓ Health: HTTP /healthz -> 200
  ✓ Agent: Agent replied: 'OK Carnitas'
Done.
```

Exit code is 0 on success. If the agent reply is missing or an error message, check gateway logs and `config/google-credentials.json`.

## Project structure

```
openclaw-agent/
├── config/
│   ├── openclaw.json          # Gateway config: bind, HTTP responses, default model (google-vertex/gemini-2.0-flash)
│   └── google-credentials.json   # Google Vertex service account JSON (gitignored; you create this)
├── scripts/
│   ├── entrypoint.sh          # Container entrypoint: writes auth-profiles for Vertex, optional creds from env
│   └── run.py                 # Run by `npm run test`: WebSocket + health checks + one agent request via /v1/responses
├── src/
│   └── openclaw_agent/        # Python package
│       ├── __init__.py
│       └── client.py          # run_agent_query(), run_agent_query_sync() using openclaw-sdk
├── tests/                     # Pytest tests (gateway connection, etc.)
├── .env                       # Local env (gitignored): OPENCLAW_GATEWAY_TOKEN, optional GOOGLE_APPLICATION_CREDENTIALS_JSON
├── .env.example               # Template for .env
├── docker-compose.yml         # OpenClaw gateway service (port 18789), volumes, env for Vertex
├── package.json               # npm scripts: start, stop, test
├── pyproject.toml             # Poetry: deps (openclaw-sdk), package layout, pytest
└── poetry.lock                # Locked dependency versions
```

| Path | Purpose |
|------|--------|
| `config/openclaw.json` | Gateway config: bind address, Control UI, HTTP `/v1/responses` enabled, default model `google-vertex/gemini-2.0-flash`. |
| `config/google-credentials.json` | Google Cloud service account JSON for Vertex (gitignored). Create this file so the gateway can call Gemini. |
| `scripts/entrypoint.sh` | Docker entrypoint: creates `auth-profiles.json` for google-vertex when missing; optionally writes credentials from `GOOGLE_APPLICATION_CREDENTIALS_JSON`. |
| `scripts/run.py` | Used by `npm run test`: WebSocket + health checks + one agent request via `POST /v1/responses`. |
| `src/openclaw_agent/` | Python package: `run_agent_query()`, `run_agent_query_sync()` in `client.py`. |
| `tests/` | Pytest tests (e.g. gateway connection). |
| `docker-compose.yml` | Defines `openclaw-gateway` service, image pin, volumes (config + credentials), env (token, Vertex ADC). |
| `package.json` | npm scripts: `start` (gateway), `stop`, `test` (run.py). |
| `pyproject.toml` | Poetry project: Python 3.11+, openclaw-sdk, pytest; package lives under `src/`. |

## npm scripts

| Script | Action |
|--------|--------|
| `npm run start` | Starts the OpenClaw gateway in Docker in the foreground (`docker compose up openclaw-gateway`). Stop with **Ctrl+C** or `npm run stop`. Run this before `npm run test` in another terminal if the gateway is not already running. |
| `npm run stop` | Stops and removes the gateway containers (`docker compose down`). |
| `npm run test` | Runs `poetry install` and `scripts/run.py` — connection checks + one agent query. Exits 0 if the agent replies. |
## Python usage

Install with Poetry (editable install so `openclaw_agent` is importable):

```bash
poetry install
```

Use the client (gateway must be running, e.g. after `npm run start`):

```python
from openclaw_agent import run_agent_query

# Async
import asyncio
result = asyncio.run(run_agent_query("What is 2+2?", agent_id="main"))
print(result)

# Or use the sync helper
from openclaw_agent.client import run_agent_query_sync
result = run_agent_query_sync("Hello", agent_id="main")
```

Or use the SDK directly:

```python
import asyncio
from openclaw_sdk import OpenClawClient

async def main():
    async with OpenClawClient.connect() as client:
        agent = client.get_agent("main")
        result = await agent.execute("Summarize the weather.")
        print(result.content)

asyncio.run(main())
```

## Configuration

**Gateway token**  
The SDK must send the same token the gateway expects. Default for local dev is `dev-token-local-only`; override with `OPENCLAW_GATEWAY_TOKEN` (in `.env` or the environment) for both `npm run start` and `npm run test`.

**Gateway URL**  
The SDK connects to the gateway by default at `ws://127.0.0.1:18789/gateway`. This project sets `OPENCLAW_GATEWAY_WS_URL=ws://127.0.0.1:18789` when running `npm run test` so the client uses the root path (some gateway setups serve WebSocket on the root). Override with env: `OPENCLAW_GATEWAY_WS_URL`.

So with `npm run start` (gateway on 18789), no extra config is needed for local runs. The gateway is started with `OPENCLAW_GATEWAY_BIND=lan` so it accepts connections from the host when run in Docker.

## Stopping the gateway

Press **Ctrl+C** in the terminal where `npm run start` is running, or run `npm run stop` from any terminal to stop and remove the containers.

## Security — before you push

To avoid leaking secrets to GitHub:

- **Do not commit** `.env` or `config/google-credentials.json`. Both are listed in `.gitignore`.
- **Verify** before pushing:
  ```bash
  git status
  ```
  Ensure `.env` and `config/google-credentials.json` do **not** appear. If they appear, run `git restore --staged .` and `git checkout -- .env config/google-credentials.json` (or remove them from the commit), and confirm they are in `.gitignore`.
- Use **`.env.example`** as a template only (no real keys). Copy to `.env` locally and fill in secrets; `.env` is gitignored.

## References

- [OpenClaw](https://openclaw.ai) — framework and docs
- [openclaw-sdk on PyPI](https://pypi.org/project/openclaw-sdk/) — Python SDK
- [OpenClaw Docker install](https://docs.openclaw.ai/install/docker) — official Docker setup
