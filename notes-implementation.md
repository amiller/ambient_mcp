# MCP Server with HTTPS and OAuth 2.1 Implementation Notes

## Overview
This project implements a secure MCP (Model Context Protocol) server with HTTPS encryption via Let's Encrypt SSL certificates and OAuth 2.1 authentication with Dynamic Client Registration (DCR).

## Architecture

```
External Traffic → mcp.ln.soc1024.com:80 → localhost:9100 (OAuth Proxy with SSL) → localhost:9101/mcp (MCP Server)
```

## Key Components

### 1. OAuth Proxy Server (`oauth_mcp_proxy.py`)
- **Port**: 9100 (HTTPS with SSL certificates)
- **Purpose**: Handles OAuth 2.1 authentication and SSL termination
- **Key Features**:
  - Dynamic Client Registration (RFC 7591)
  - OAuth 2.1 authorization code flow with PKCE
  - Discovery endpoints (`.well-known/oauth-authorization-server`)
  - Token management and validation
  - Request proxying to MCP server

### 2. MCP Server (`ambient_mcp_server.py`)
- **Port**: 9101 (HTTP, behind proxy)
- **Purpose**: Provides ambient insights and conversation analysis tools
- **Transport**: FastMCP streamable-http
- **Tools Available**:
  - `log_conversation_turn`: Log conversation exchanges for analysis
  - `get_user_context`: Retrieve user interests, projects, preferences
  - `get_recent_insights`: Get recent conversation insights
  - `add_user_interest`: Manually add user interests
  - `set_user_goal`: Add or update user goals

### 3. SSL Certificates (`./certs/`)
- **Source**: Let's Encrypt via certbot
- **Files**: `fullchain.pem`, `privkey.pem`
- **Domain**: mcp.ln.soc1024.com
- **Challenge**: HTTP-01 on port 9100

## Implementation Timeline

### Phase 1: Initial SSL Setup
- Installed certbot in virtual environment
- Obtained Let's Encrypt certificates using HTTP-01 challenge
- Initial attempts to add SSL directly to FastMCP (unsuccessful)

### Phase 2: OAuth Discovery
- Discovered Claude requires OAuth 2.1 with DCR
- Found "Field Required" errors were actually 404 responses misinterpreted
- Realized need for separate OAuth proxy layer

### Phase 3: OAuth Proxy Implementation
- Created complete OAuth 2.1 server using Flask + Authlib
- Implemented all required endpoints:
  - `/oauth/authorize` - Authorization endpoint
  - `/oauth/token` - Token exchange endpoint
  - `/register` - Dynamic Client Registration
  - `/.well-known/oauth-authorization-server` - Discovery

### Phase 4: MCP Server Configuration
- Fixed transport configuration to use `streamable-http`
- Configured server to run on HTTP behind SSL proxy
- Resolved route precedence issues in proxy

### Phase 5: Integration & Testing
- Successfully integrated OAuth proxy with MCP server
- Verified all tools working correctly
- Documented minor timeout issues with file I/O operations

## Key Technical Decisions

### Why Separate OAuth Proxy?
- FastMCP doesn't natively support SSL configuration parameters
- Separation of concerns: authentication vs business logic
- Easier to debug and maintain
- Allows MCP server to focus on core functionality

### Why OAuth 2.1 + DCR?
- Required by Claude for MCP server authentication
- DCR allows dynamic client registration without pre-configuration
- PKCE provides additional security for authorization code flow

### Transport Choice: streamable-http
- Initial attempts with SSE transport and uvicorn failed
- FastMCP's streamable-http provides proper MCP protocol support
- Generates correct 200/202 responses instead of 404s

## Files Created/Modified

### New Files:
- `oauth_mcp_proxy.py` - Complete OAuth 2.1 proxy server
- `./certs/fullchain.pem` - Let's Encrypt SSL certificate
- `./certs/privkey.pem` - Let's Encrypt private key
- `./certbot-logs/letsencrypt.log` - Certificate generation logs

### Modified Files:
- `ambient_mcp_server.py` - Updated SSL config and transport
- `requirements.txt` - Added authlib, flask, requests

## Current Status
✅ HTTPS working via Let's Encrypt certificates
✅ OAuth 2.1 authentication functioning properly
✅ MCP server responding correctly with 200/202 status codes
✅ All tools functioning (get_user_context, set_user_goal, add_user_interest)
⚠️ Minor intermittent timeout on get_recent_insights tool due to file I/O

## Lessons Learned

1. **Don't guess at errors** - Systematic log analysis revealed the true cause of "Field Required" errors
2. **Separation of concerns** - OAuth proxy + MCP server architecture proved more maintainable than monolithic approach
3. **Transport matters** - FastMCP transport selection critical for proper protocol compliance
4. **Route ordering** - Flask route precedence affects request handling flow

## Future Considerations

- Consider database storage for production instead of in-memory/file storage
- Implement token refresh flow for long-lived sessions
- Add rate limiting and additional security measures
- Monitor file I/O performance for insights operations