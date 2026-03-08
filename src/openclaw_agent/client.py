"""OpenClaw client wrapper for running agent queries."""

import asyncio
from typing import Optional

from openclaw_sdk import OpenClawClient


async def run_agent_query(
    query: str,
    agent_id: str = "main",
    session_name: str = "main",
) -> Optional[str]:
    """
    Execute a query against an OpenClaw agent.

    Requires a running OpenClaw gateway at ws://127.0.0.1:18789/gateway
    (or OPENCLAW_GATEWAY_WS_URL).

    Args:
        query: The prompt or question to send to the agent.
        agent_id: OpenClaw agent identifier (default "main").
        session_name: Session name for conversation scope (default "main").

    Returns:
        The agent's text response, or None if execution failed.
    """
    client = await OpenClawClient.connect()
    async with client:
        agent = client.get_agent(agent_id, session_name=session_name)
        result = await agent.execute(query)
        return result.content if result.success else None


def run_agent_query_sync(
    query: str,
    agent_id: str = "main",
    session_name: str = "main",
) -> Optional[str]:
    """Synchronous wrapper for run_agent_query."""
    return asyncio.run(run_agent_query(query, agent_id, session_name))
