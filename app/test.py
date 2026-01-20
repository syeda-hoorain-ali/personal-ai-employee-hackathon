from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
from starlette.requests import Request
import os
from datetime import datetime

# Create server instance using the official SDK
mcp = FastMCP(
    name=os.getenv("MCP_SERVER_NAME", "example-mcp-server"),
    json_response=True
)

@mcp.custom_route("/", methods=[""])
async def health_check(request: Request):
    """Health check endpoint for the server."""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": os.getenv("MCP_SERVER_NAME", "example-mcp-server"),
        "version": "1.0.0",
    })

