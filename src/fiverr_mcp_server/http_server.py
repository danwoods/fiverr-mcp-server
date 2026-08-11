"""HTTP server wrapper for MCP that exposes SSE endpoints for n8n compatibility."""

import asyncio
import json
import logging
import subprocess
import sys
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Global state for MCP subprocess and clients
mcp_process: Optional[subprocess.Popen] = None
client_queues: Dict[str, asyncio.Queue] = {}
message_id_counter = 0


class MCPMessage(BaseModel):
    """MCP protocol message."""
    jsonrpc: str = "2.0"
    id: Optional[int] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


def start_mcp_subprocess():
    """Start the MCP server subprocess in stdio mode."""
    global mcp_process
    if mcp_process is None or mcp_process.poll() is not None:
        mcp_process = subprocess.Popen(
            [sys.executable, "-m", "fiverr_mcp_server.server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={"TRANSPORT": "stdio"},
        )
    return mcp_process


def send_mcp_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Send a message to the MCP server and receive a response."""
    global mcp_process, message_id_counter
    
    process = start_mcp_subprocess()
    
    if "id" not in message:
        message_id_counter += 1
        message["id"] = message_id_counter
    
    if "jsonrpc" not in message:
        message["jsonrpc"] = "2.0"
    
    try:
        # Send message to subprocess
        message_bytes = (json.dumps(message) + "\n").encode()
        process.stdin.write(message_bytes)
        process.stdin.flush()
        
        # Read response
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.decode())
            return response
        else:
            return {"jsonrpc": "2.0", "id": message.get("id"), "error": {"code": -32603, "message": "Internal error"}}
    except Exception as e:
        logger.error(f"Error communicating with MCP server: {e}")
        return {"jsonrpc": "2.0", "id": message.get("id"), "error": {"code": -32603, "message": str(e)}}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage MCP subprocess lifecycle."""
    start_mcp_subprocess()
    yield
    if mcp_process:
        mcp_process.terminate()
        try:
            mcp_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            mcp_process.kill()


app = FastAPI(title="Fiverr MCP Server", lifespan=lifespan)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Fiverr MCP Server"}


@app.get("/mcp")
async def mcp_sse():
    """SSE endpoint for n8n MCP Client node."""
    
    async def event_generator():
        """Stream MCP protocol messages as SSE."""
        try:
            # Send initialize request
            init_response = send_mcp_message({
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "n8n",
                        "version": "1.0"
                    }
                }
            })
            
            yield f'data: {json.dumps(init_response)}\n\n'
            
            # Send list_tools request to discover available tools
            tools_response = send_mcp_message({
                "method": "tools/list",
                "params": {}
            })
            
            yield f'data: {json.dumps(tools_response)}\n\n'
            
            # Keep connection alive with periodic heartbeats
            heartbeat_count = 0
            while heartbeat_count < 60:  # Keep alive for ~5 minutes
                await asyncio.sleep(5)
                heartbeat_count += 1
                # Send a simple notification to keep connection alive
                yield f'data: {json.dumps({"type": "notification"})}\n\n'
                
        except Exception as e:
            logger.error(f"Error in SSE stream: {e}")
            yield f'data: {json.dumps({"error": str(e)})}\n\n'
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@app.post("/mcp/message")
async def mcp_message(message: Dict[str, Any]):
    """Handle MCP protocol messages from n8n."""
    try:
        # Send message to MCP server and return response
        response = send_mcp_message(message)
        return response
    except Exception as e:
        logger.error(f"Error handling MCP message: {e}")
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "error": {"code": -32603, "message": str(e)}
        }


def run_http_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the HTTP server."""
    import uvicorn
    
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_http_server()

