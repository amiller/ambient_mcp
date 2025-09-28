#!/usr/bin/env python3
"""
Start both OAuth proxy and MCP server in a single container
"""

import subprocess
import sys
import time
import signal
import os

def signal_handler(sig, frame):
    print("\nShutting down services...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    print("Starting MCP services...")

    # Set environment variables for Docker deployment
    os.environ["USE_SSL"] = "false"
    os.environ["OAUTH_HOST"] = "0.0.0.0"
    os.environ["MCP_HOST"] = "127.0.0.1"

    # Start MCP server in background
    mcp_process = subprocess.Popen([
        sys.executable, "ambient_mcp_server.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Give MCP server time to start
    time.sleep(2)

    # Start OAuth proxy in foreground
    try:
        oauth_process = subprocess.Popen([
            sys.executable, "oauth_mcp_proxy.py"
        ])
        oauth_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Clean up processes
        mcp_process.terminate()
        mcp_process.wait()

if __name__ == "__main__":
    main()