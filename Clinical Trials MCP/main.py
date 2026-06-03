import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from agents import Agent, Runner
from agents.mcp import MCPServerManager, MCPServerStreamableHttp

load_dotenv(Path(__file__).resolve().parent / ".env")

logger = logging.getLogger(__name__)

# (display_name, streamable HTTP MCP URL)
MCP_ENDPOINTS: list[tuple[str, str]] = [
    ("biorxiv", "https://hcls.mcp.claude.com/biorxiv/mcp"),
    ("clinical trials", "https://hcls.mcp.claude.com/clinical_trials/mcp"),
    ("pubmed", "https://pubmed.mcp.claude.com/mcp"),
]

basic_instructions = """
You are a highly intelligent medical research assistant with access to specialized tools.

**Tool Usage:**
- Automatically select the most relevant tool based on user intent — never ask which tool to use.
- If the query involves research or studies, fetch from PubMed or BioRxiv.
- If the query involves ongoing or completed trials, fetch from clinical trial databases.
- If multiple tools are relevant, call them in parallel and synthesize the results.

**Response Standards:**
- Always return structured, accurate, and evidence-based insights.
- Cite sources with paper titles, authors, and publication dates where applicable.
- Clearly distinguish between research findings and clinical trial outcomes.
- Never speculate — if data is insufficient, state it explicitly.
"""


async def main():
    if not os.environ.get("OPENAI_API_KEY"):
        print(
            "Missing OPENAI_API_KEY. Add it to a .env file in this folder:\n"
            "  OPENAI_API_KEY=sk-...\n"
            "Or set the environment variable in your shell before running python main.py.",
            file=sys.stderr,
        )
        sys.exit(1)

    servers = [
        MCPServerStreamableHttp(name=name, params={"url": url})
        for name, url in MCP_ENDPOINTS
    ]

    for name, url in MCP_ENDPOINTS:
        logger.info("Configured MCP server name=%r url=%s", name, url)

    async with MCPServerManager(servers) as manager:
        active = manager.active_servers
        logger.info(
            "MCP connect finished: active=%d failed=%d",
            len(active),
            len(manager.failed_servers),
        )
        for s in manager.all_servers:
            url = s.params.get("url", "?")  # type: ignore[attr-defined]
            ok = s in active
            logger.info(
                "MCP server name=%r url=%s connected=%s",
                s.name,
                url,
                ok,
            )
        for failed in manager.failed_servers:
            err = manager.errors.get(failed)
            url = failed.params.get("url", "?")  # type: ignore[attr-defined]
            logger.warning(
                "MCP server failed to connect name=%r url=%s error=%s",
                failed.name,
                url,
                err,
            )

        agent = Agent(
            name="Medical Research Assistant",
            instructions=basic_instructions,
            model="gpt-5-mini",
            mcp_servers=active,
        )

        query = "Latest clinical trials and research papers on diabetes treatment"

        logger.info("Running agent query: %s", query)
        result = await Runner.run(agent, query)
        print(result.final_output)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(main())


