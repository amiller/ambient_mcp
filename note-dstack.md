# Dstack Deployment Notes

## Overview
Successfully deployed MCP server with OAuth 2.1 authentication to Phala's dstack TEE platform.

## Architecture
```
External HTTPS → dstack-gateway → OAuth Proxy (port 9100) → MCP Server (port 9101)
```

## Deployment Process

### 1. Docker Setup
- Created unified scripts using environment variables instead of duplicates
- Built image: `docker build -t mcp-server .`
- Tagged: `docker tag mcp-server socrates1024/mcp-server`
- Pushed: `docker push socrates1024/mcp-server`
- Got SHA256: `socrates1024/mcp-server@sha256:d387afedbafd8f1664ddd05c99c216ee0ca3cb3cbc422ef82940fe52726e0d06`

### 2. Dstack Deployment
```bash
phala deploy docker-compose-deploy.yml --node 3
```

### 3. Deployment Details
- **CVM ID**: 882b39b2-8e76-417f-9d18-8709826b8ef3
- **App ID**: f2b83caf0bc23554b22f3bddcc8a3e64471df7ab
- **Node**: 3 (prod5) - no on-chain KMS required
- **URL**: https://f2b83caf0bc23554b22f3bddcc8a3e64471df7ab-9100.dstack-prod5.phala.network

### 4. Key Files
- `docker-compose.yml` - Development with inline build
- `docker-compose-deploy.yml` - Production referencing pushed image by SHA256
- `start_services.py` - Service orchestrator with environment-based config

### 5. Environment Variables
- `USE_SSL=false` - dstack-gateway handles HTTPS termination
- `OAUTH_HOST=0.0.0.0` - Bind to all interfaces in container
- `MCP_HOST=127.0.0.1` - Internal MCP server binding

### 6. Verification
- OAuth discovery: `/.well-known/oauth-authorization-server` ✓
- MCP protocol: Responds correctly to JSON-RPC over SSE ✓
- HTTPS: Accessible via dstack-gateway ✓

## Status: ✅ DEPLOYED & WORKING