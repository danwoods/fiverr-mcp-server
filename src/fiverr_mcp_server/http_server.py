"""HTTP server wrapper for MCP that exposes SSE endpoints for n8n compatibility."""

import asyncio
import json
import os
from typing import Optional

from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from mcp.client.sse import SSEClientTransport
from mcp.client.stdio import StdioClientTransport

from fiverr_mcp_server.mcp_server import mcp
import fiverr_mcp_server.tools  # noqa: F401 - registers tools


app = FastAPI(title="Fiverr MCP Server")

# Global transport to keep the subprocess alive
mcp_transport = None


async def get_mcp_transport():
    """Get or create the MCP transport."""
    global mcp_transport
    if mcp_transport is None:
        # Create a subprocess transport that runs the MCP server via stdio
        mcp_transport = StdioClientTransport(mcp.run)
    return mcp_transport


@app.on_event("startup")
async def startup():
    """Initialize MCP connection on startup."""
    await get_mcp_transport()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Fiverr MCP Server"}


@app.get("/mcp")
async def mcp_sse():
    """SSE endpoint for n8n MCP Client node."""
    
    async def event_generator():
        """Stream MCP messages as SSE events."""
        transport = await get_mcp_transport()
        
        try:
            # For now, send a simple heartbeat
            # In a full implementation, this would stream actual MCP protocol messages
            while True:
                yield 'data: {"type": "heartbeat"}\n\n'
                await asyncio.sleep(30)
        except Exception as e:
            yield f'data: {{"type": "error", "message": "{str(e)}"}}\n\n'
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/mcp/message")
async def mcp_message(data: dict):
    """Handle MCP protocol messages from n8n."""
    try:
        transport = await get_mcp_transport()
        
        # Echo the message back with a simple response
        return {
            "type": "response",
            "id": data.get("id"),
            "result": {"status": "received"},
        }
    except Exception as e:
        return {"type": "error", "message": str(e)}, 500


def run_http_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the HTTP server."""
    import uvicorn
    
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_http_server()

