# Secure MCP Server with OAuth 2.1

A self-contained MCP (Model Context Protocol) server implementation with HTTPS encryption and OAuth 2.1 authentication.

## Quick Start

1. **Install dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Generate SSL certificates** (if needed):
   ```bash
   # Ensure port 9100 is routed from your domain
   certbot certonly --standalone --preferred-challenges http -d yourdomain.com --http-01-port 9100
   # Copy certificates to ./certs/
   ```

3. **Start the servers**:
   ```bash
   # Terminal 1: OAuth proxy (HTTPS on port 9100)
   python oauth_mcp_proxy.py

   # Terminal 2: MCP server (HTTP on port 9101)
   python ambient_mcp_server.py
   ```

## Architecture

```
External Requests → Domain:80 → localhost:9100 (OAuth Proxy + SSL) → localhost:9101 (MCP Server)
```

## Components

### OAuth Proxy (`oauth_mcp_proxy.py`)
- Handles HTTPS/SSL termination
- Implements OAuth 2.1 with Dynamic Client Registration
- Proxies authenticated requests to MCP server
- Runs on port 9100

### MCP Server (`ambient_mcp_server.py`)
- Provides conversation analysis and user context tools
- Runs on HTTP port 9101 behind the proxy
- Uses FastMCP with streamable-http transport

## Available Tools

- `log_conversation_turn` - Log conversations for analysis
- `get_user_context` - Get user interests and preferences
- `get_recent_insights` - Retrieve recent conversation insights
- `add_user_interest` - Add user interests
- `set_user_goal` - Set user goals

## Configuration

### Domain Setup
Route external traffic from your domain to localhost:9100. For example:
- `mcp.yourdomain.com:80` → `localhost:9100`

### SSL Certificates
Place Let's Encrypt certificates in `./certs/`:
- `fullchain.pem` - Certificate chain
- `privkey.pem` - Private key

### MCP Server URL
Update `MCP_SERVER_URL` in `oauth_mcp_proxy.py` if needed:
```python
MCP_SERVER_URL = "http://127.0.0.1:9101/mcp"
```

## OAuth Endpoints

- `/.well-known/oauth-authorization-server` - Discovery
- `/oauth/authorize` - Authorization
- `/oauth/token` - Token exchange
- `/register` - Dynamic client registration

## Files

- `oauth_mcp_proxy.py` - OAuth 2.1 proxy server
- `ambient_mcp_server.py` - MCP server with insights tools
- `requirements.txt` - Python dependencies
- `./certs/` - SSL certificates directory
- `./mcp_data/` - MCP server data storage
- `IMPLEMENTATION_NOTES.md` - Detailed implementation notes

## Security Features

- HTTPS encryption via Let's Encrypt
- OAuth 2.1 with PKCE
- Dynamic Client Registration (RFC 7591)
- Token-based authentication
- Request proxying with header filtering

## Development

See `IMPLEMENTATION_NOTES.md` for detailed implementation history and technical decisions.