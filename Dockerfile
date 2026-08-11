FROM python:3.13-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project
COPY . .

# Install dependencies with uv
RUN uv sync --no-dev --no-editable

# Run the MCP server
CMD ["uv", "run", "fiverr-mcp-server"]

