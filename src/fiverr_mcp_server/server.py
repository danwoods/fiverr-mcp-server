import os

from fiverr_mcp_server.mcp_server import mcp
import fiverr_mcp_server.tools  # noqa: F401 - registers tools


def main():
    transport = os.getenv("TRANSPORT", "stdio").lower()
    
    if transport == "http":
        # Run as HTTP server for n8n integration
        from fiverr_mcp_server.http_server import run_http_server
        port = int(os.getenv("PORT", 8000))
        run_http_server(host="0.0.0.0", port=port)
    else:
        # Run with stdio or sse transport
        mcp.run(transport=transport)


if __name__ == "__main__":
    main()

