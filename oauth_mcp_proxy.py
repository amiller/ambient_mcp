#!/usr/bin/env python3
"""
Simple OAuth 2.1 proxy for MCP servers with Dynamic Client Registration
Self-contained implementation using Authlib and Flask
"""

import json
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify, Response
from authlib.oauth2 import OAuth2Error
from authlib.oauth2.rfc6749 import grants
from authlib.oauth2.rfc7591 import ClientRegistrationEndpoint
from authlib.oauth2.rfc6749.models import ClientMixin, AuthorizationCodeMixin
from authlib.integrations.flask_oauth2 import AuthorizationServer
import requests

# Simple in-memory storage (use a database in production)
clients_db = {}
codes_db = {}
tokens_db = {}

class Client(ClientMixin):
    def __init__(self, client_id, client_secret, **kwargs):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uris = kwargs.get('redirect_uris', [])
        self.grant_types = kwargs.get('grant_types', ['authorization_code'])
        self.response_types = kwargs.get('response_types', ['code'])
        self.scope = kwargs.get('scope', '')
        self.client_name = kwargs.get('client_name', '')

    def get_client_id(self):
        return self.client_id

    def get_default_redirect_uri(self):
        return self.redirect_uris[0] if self.redirect_uris else None

    def get_allowed_scope(self, scope):
        return scope

    def check_redirect_uri(self, redirect_uri):
        return redirect_uri in self.redirect_uris

    def has_client_secret(self):
        return bool(self.client_secret)

    def check_client_secret(self, client_secret):
        return self.client_secret == client_secret

    def check_token_endpoint_auth_method(self, method):
        return method in ['client_secret_basic', 'client_secret_post', 'none']

    def check_response_type(self, response_type):
        return response_type in self.response_types

    def check_grant_type(self, grant_type):
        return grant_type in self.grant_types

class AuthorizationCode(AuthorizationCodeMixin):
    def __init__(self, code, client_id, redirect_uri, scope, user_id, **kwargs):
        self.code = code
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.user_id = user_id
        self.code_challenge = kwargs.get('code_challenge')
        self.code_challenge_method = kwargs.get('code_challenge_method')
        self.auth_time = time.time()

    def is_expired(self):
        return time.time() - self.auth_time > 600  # 10 minutes

    def get_redirect_uri(self):
        return self.redirect_uri

    def get_scope(self):
        return self.scope

class MyClientRegistrationEndpoint(ClientRegistrationEndpoint):
    def authenticate_token(self, request):
        # For simplicity, allow all registrations
        return True

    def save_client(self, client_info, client_metadata, request):
        client_id = client_info['client_id']
        client_secret = client_info.get('client_secret')

        client = Client(
            client_id=client_id,
            client_secret=client_secret,
            **client_metadata
        )
        clients_db[client_id] = client
        return client

    def get_server_metadata(self):
        return {
            "grant_types_supported": ["authorization_code"],
            "response_types_supported": ["code"],
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post", "none"]
        }

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)

# OAuth2 server setup
authorization = AuthorizationServer(app)

def query_client(client_id):
    return clients_db.get(client_id)

def save_authorization_code(code, request):
    codes_db[code] = AuthorizationCode(
        code=code,
        client_id=request.client.client_id,
        redirect_uri=request.redirect_uri,
        scope=request.scope,
        user_id='default_user',
        code_challenge=getattr(request, 'code_challenge', None),
        code_challenge_method=getattr(request, 'code_challenge_method', None)
    )

def query_authorization_code(code, client):
    auth_code = codes_db.get(code)
    if auth_code and auth_code.client_id == client.client_id:
        return auth_code
    return None

def delete_authorization_code(authorization_code):
    if authorization_code.code in codes_db:
        del codes_db[authorization_code.code]

def save_token(token, request):
    token_key = token['access_token']
    tokens_db[token_key] = {
        'client_id': request.client.client_id,
        'user_id': getattr(request, 'user_id', 'default_user'),
        'scope': token.get('scope', ''),
        'expires_at': time.time() + token.get('expires_in', 3600)
    }

authorization.init_app(app, query_client=query_client, save_token=save_token)

# Register authorization code grant
class AuthorizationCodeGrant(grants.AuthorizationCodeGrant):
    def save_authorization_code(self, code, request):
        save_authorization_code(code, request)

    def query_authorization_code(self, code, client):
        return query_authorization_code(code, client)

    def delete_authorization_code(self, authorization_code):
        delete_authorization_code(authorization_code)

    def authenticate_user(self, authorization_code):
        return {'id': authorization_code.user_id}

authorization.register_grant(AuthorizationCodeGrant)

# Register client registration endpoint
client_registration = MyClientRegistrationEndpoint()
authorization.register_endpoint(client_registration)

# OAuth discovery endpoints
@app.route('/.well-known/oauth-authorization-server')
def oauth_authorization_server():
    return jsonify({
        "issuer": request.host_url.rstrip('/'),
        "authorization_endpoint": request.host_url.rstrip('/') + "/oauth/authorize",
        "token_endpoint": request.host_url.rstrip('/') + "/token",
        "registration_endpoint": request.host_url.rstrip('/') + "/register",
        "grant_types_supported": ["authorization_code"],
        "response_types_supported": ["code"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post", "none"]
    })

@app.route('/.well-known/oauth-protected-resource')
def oauth_protected_resource():
    return jsonify({
        "resource": request.host_url.rstrip('/'),
        "authorization_servers": [request.host_url.rstrip('/')]
    })

# OAuth endpoints
@app.route('/oauth/authorize', methods=['GET', 'POST'])
def authorize():
    if request.method == 'GET':
        # Auto-approve for simplicity
        try:
            grant = authorization.get_consent_grant(end_user='default_user')
            return authorization.create_authorization_response(grant=grant)
        except OAuth2Error as error:
            return jsonify(error.get_body()), error.status_code

    # Handle POST (not needed for our simple case)
    return jsonify({"error": "invalid_request"}), 400

@app.route('/oauth/token', methods=['POST'])
def issue_token():
    return authorization.create_token_response()

@app.route('/register', methods=['POST'])
def register_client():
    try:
        # Simple DCR implementation
        data = request.get_json() or {}

        # Generate client credentials
        client_id = secrets.token_urlsafe(32)
        client_secret = secrets.token_hex(24)

        # Use provided redirect URIs or Claude's default
        redirect_uris = data.get('redirect_uris', ['https://claude.ai/api/mcp/auth_callback'])
        grant_types = data.get('grant_types', ['authorization_code'])
        response_types = data.get('response_types', ['code'])

        # Create and store client
        client = Client(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uris=redirect_uris,
            grant_types=grant_types,
            response_types=response_types,
            scope=data.get('scope', ''),
            client_name=data.get('client_name', 'MCP Client')
        )
        clients_db[client_id] = client

        # Return client registration response
        response = {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_id_issued_at": int(time.time()),
            "client_secret_expires_at": 0,  # Never expires
            "redirect_uris": redirect_uris,
            "grant_types": grant_types,
            "response_types": response_types,
            "token_endpoint_auth_method": "client_secret_basic"
        }

        if data.get('client_name'):
            response['client_name'] = data['client_name']
        if data.get('scope'):
            response['scope'] = data['scope']

        return jsonify(response), 201

    except Exception as e:
        return jsonify({"error": "server_error", "error_description": str(e)}), 500

# Add token endpoint at root for compatibility
@app.route('/token', methods=['POST'])
def issue_token_alt():
    return authorization.create_token_response()

# Handle token exchange at root path (what Claude seems to be using)
@app.route('/', methods=['POST'])
def handle_root_post():
    print(f"ROOT POST - Content-Type: {request.content_type}")
    print(f"ROOT POST - Form data: {dict(request.form)}")
    print(f"ROOT POST - JSON data: {request.get_json()}")
    print(f"ROOT POST - Raw data: {request.get_data()}")
    print(f"ROOT POST - Headers: {dict(request.headers)}")

    # Check if this is a token request
    if request.content_type and 'application/x-www-form-urlencoded' in request.content_type:
        form_data = request.form
        if 'grant_type' in form_data and form_data['grant_type'] == 'authorization_code':
            print("Detected token request, calling authorization.create_token_response()")
            return authorization.create_token_response()

    # Otherwise treat as regular proxy request
    print("Not a token request, proxying to MCP")
    return proxy_to_mcp('')

# Proxy to MCP server
MCP_SERVER_URL = "http://127.0.0.1:9101/mcp"

def verify_token(token):
    """Verify the access token"""
    if not token:
        return False

    token_info = tokens_db.get(token)
    if not token_info:
        return False

    if time.time() > token_info['expires_at']:
        del tokens_db[token]
        return False

    return True

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/', defaults={'path': ''}, methods=['GET', 'PUT', 'DELETE', 'PATCH'])
def proxy_to_mcp(path):
    # Skip auth for OAuth endpoints
    if (path.startswith('.well-known/') or
        path.startswith('oauth/') or
        path == 'register' or
        path == 'token'):
        return jsonify({"error": "not_found"}), 404

    # For now, skip authentication since Claude handles OAuth differently
    # TODO: Implement proper token validation based on Claude's OAuth flow
    # auth_header = request.headers.get('Authorization', '')
    # if not auth_header.startswith('Bearer '):
    #     return jsonify({"error": "unauthorized", "error_description": "Missing or invalid authorization header"}), 401

    # token = auth_header[7:]  # Remove 'Bearer '
    # if not verify_token(token):
    #     return jsonify({"error": "unauthorized", "error_description": "Invalid or expired token"}), 401

    # Proxy request to MCP server
    try:
        url = f"{MCP_SERVER_URL}/{path}" if path else MCP_SERVER_URL
        resp = requests.request(
            method=request.method,
            url=url,
            headers={k: v for k, v in request.headers if k.lower() != 'host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            verify=False  # Skip SSL verification for localhost
        )

        # Return response
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                  if name.lower() not in excluded_headers]

        response = Response(resp.content, resp.status_code, headers)
        return response

    except Exception as e:
        return jsonify({"error": "server_error", "error_description": str(e)}), 500

if __name__ == "__main__":
    # Run on port 9100 to match your domain routing
    app.run(host="127.0.0.1", port=9100, debug=True, ssl_context=('./certs/fullchain.pem', './certs/privkey.pem'))