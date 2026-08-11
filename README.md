# Fiverr MCP Server

[![PyPI version](https://badge.fury.io/py/fiverr-mcp-server.svg)](https://pypi.org/project/fiverr-mcp-server/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

mcp-name: io.github.KyuRish/fiverr-mcp-server

MCP server for searching and browsing Fiverr - gigs, sellers, pricing, and reviews. No API key required.

## Features

- **Search gigs** by keyword with filters (price, seller level, category, sorting)
- **Get gig details** including pricing packages (Basic/Standard/Premium), description, and tags
- **View seller profiles** with certifications, languages, hourly rate, and gig listings
- **Read gig reviews** from the first page of any gig
- **List categories** to discover valid category slugs for filtered search
- All prices returned in **USD** (not cents)
- Built-in **rate limiting** and retry with browser fingerprint rotation
- Structured **error messages** on failures (no raw crashes)
- **HTTP server mode** for integration with n8n and other platforms

## Installation

### Using uvx (recommended)

```json
{
  "mcpServers": {
    "fiverr": {
      "command": "uvx",
      "args": ["fiverr-mcp-server"]
    }
  }
}
```

### Using pip

```bash
pip install fiverr-mcp-server
```

### From source

```bash
git clone https://github.com/KyuRish/fiverr-mcp-server.git
cd fiverr-mcp-server
uv sync
uv run fiverr-mcp-server
```

## Configuration

Add to your Claude Desktop config (`claude_desktop_config.json`):

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "fiverr": {
      "command": "uvx",
      "args": ["fiverr-mcp-server"]
    }
  }
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TRANSPORT` | Transport mode (`stdio`, `sse`, or `http`) | `stdio` |
| `PORT` | Port for HTTP server (only used with `TRANSPORT=http`) | `8000` |
| `PROXY_URL` | Optional HTTP proxy for requests | - |
| `RATE_LIMIT_DELAY` | Minimum seconds between requests | `2` |

### Using with n8n

To use this server with n8n's MCP Client node, run it in HTTP mode:

```bash
TRANSPORT=http PORT=8000 uv run fiverr-mcp-server
```

Then configure your n8n MCP Client credentials:
- **Connection Type:** SSE
- **URL:** `http://your-server:8000/mcp`
- **No authentication needed**

## Available Tools

### `search_gigs`
Search the Fiverr marketplace by keyword. Returns up to 48 gigs per page with pagination info.

**Parameters:**
- `query` (required) - Search query (e.g. "logo design", "python developer")
- `category` - Category slug (use `list_categories` to see valid values)
- `min_price` / `max_price` - Price range filter in USD
- `seller_level` - `"level_one_seller"`, `"level_two_seller"`, or `"top_rated_seller"`
- `sort_by` - `"relevance"`, `"best_selling"`, `"newest"`, `"price_asc"`, or `"price_desc"`
- `page` - Page number for pagination

**Returns:** List of gigs with title, price (USD), rating, reviews count, seller name, and URL. Also includes `total_results` and `has_more` for pagination.

### `get_gig_details`
Get full details of a specific gig including all pricing tiers.

**Parameters:**
- `url` (required) - Fiverr gig URL or path

**Returns:** Title, description, seller info, packages (name/price/delivery/revisions/features), tags, metadata, rating, reviews count, category, and orders in queue.

### `get_seller_profile`
Get a seller's profile. Use `seller_name` from search results as the username.

**Parameters:**
- `username` (required) - Seller's Fiverr username

**Returns:** Display name, bio, location, member since, languages, certifications, hourly rate (USD), gig listings, and verification status.

### `get_gig_reviews`
Get the first page of reviews for a gig (typically 5-10 reviews loaded from the page).

**Parameters:**
- `url` (required) - Fiverr gig URL or path

**Returns:** List of reviews with buyer name, country, rating, date, and text.

### `list_categories`
List all available Fiverr category slugs for use with `search_gigs`.

**Returns:** List of category objects with `slug` and `name`.

## Workflow Examples

**Finding a freelancer:**
1. `list_categories()` - see available categories
2. `search_gigs("3D character modeling")` - browse results
3. `get_gig_details(url)` - check pricing tiers (use URL from search results)
4. `get_seller_profile(seller_name)` - review their profile (use seller_name from search results)
5. `get_gig_reviews(url)` - read reviews

## Limitations

- **Reviews** - only the first page of reviews is available (Fiverr loads more via AJAX which requires authenticated requests)
- **Rate limiting** - Fiverr may block rapid requests. A 2-second minimum delay is enforced between requests (configurable via `RATE_LIMIT_DELAY`)
- **Data freshness** - all data is scraped from public pages in real-time, not cached

## How It Works

This server extracts structured data from Fiverr's public pages by reading the Perseus SSR data blob (`<script id="perseus-initial-props">`) that Fiverr's frontend framework embeds in every page. Uses `curl_cffi` for browser TLS fingerprint impersonation to handle Cloudflare protection, with automatic retry and fingerprint rotation.

## Responsible Use

This tool is intended for personal use - finding freelancers, comparing gigs, and reading reviews through an AI assistant. Please:

- Do not use for mass data harvesting or building databases of seller information
- Do not use for automated competitive monitoring at scale
- Respect Fiverr's infrastructure by keeping the default rate limit
- Be aware that web scraping may violate Fiverr's Terms of Service

## Development

```bash
git clone https://github.com/KyuRish/fiverr-mcp-server.git
cd fiverr-mcp-server
uv sync
uv run fiverr-mcp-server
```

## License

MIT

