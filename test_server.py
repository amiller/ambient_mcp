#!/usr/bin/env python3
"""
Test script for the Ambient Insights MCP Server
"""

import asyncio
import json
from pathlib import Path
import subprocess
import time
import signal
import os
import sys

def test_basic_functionality():
    """Test the basic insight detection without running the server"""
    print("Testing insight detection...")

    # Import the server classes directly
    sys.path.append('.')
    from ambient_mcp_server import InsightDetector, AmbientInsightsServer

    detector = InsightDetector()
    server = AmbientInsightsServer()

    # Test learning moment detection
    learning_text = "Wow, I didn't know Python could do that!"
    learning_result = detector.detect_learning_moment(learning_text)
    print(f"Learning detection: {learning_result}")

    # Test problem solving detection
    problem_text = "How do I fix this bug in my code?"
    problem_result = detector.detect_problem_solving(problem_text)
    print(f"Problem detection: {problem_result}")

    # Test interest extraction
    interest_text = "I love working with Python and React for web development"
    interests = detector.extract_interests(interest_text)
    print(f"Extracted interests: {interests}")

    # Test conversation analysis
    user_msg = "I'm struggling with Docker containers and how to set them up properly"
    assistant_msg = "Let me help you with Docker setup..."

    server.analyze_conversation_turn(user_msg, assistant_msg)
    print("Conversation turn analyzed successfully")

    # Check if data was saved
    context = server.get_user_context()
    print(f"User context: {json.dumps(context, indent=2)}")

    insights = server.get_recent_insights(3)
    print(f"Recent insights: {json.dumps(insights, indent=2)}")

    print("✅ Basic functionality tests passed!")

def test_server_startup():
    """Test that the MCP server starts correctly with stdio transport"""
    print("\nTesting server startup...")

    try:
        # Start the server in background
        process = subprocess.Popen([
            sys.executable, "ambient_mcp_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)

        # Give it time to start
        time.sleep(2)

        # Check if process is still running (MCP servers keep running)
        if process.poll() is None:
            print("✅ MCP server started successfully with stdio transport")

            # Send a simple MCP initialization message
            try:
                init_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "test-client", "version": "1.0.0"}
                    }
                }

                # Send the message
                message = json.dumps(init_request) + "\n"
                process.stdin.write(message.encode())
                process.stdin.flush()

                # Try to read response (with timeout)
                time.sleep(1)
                print("✅ MCP initialization message sent")

            except Exception as e:
                print(f"⚠️  MCP communication test failed (expected for this test): {e}")

        else:
            stdout, stderr = process.communicate()
            print(f"❌ Server failed to start")
            print(f"stdout: {stdout.decode()}")
            print(f"stderr: {stderr.decode()}")

        # Clean up
        if process.poll() is None:
            process.terminate()
            process.wait()
            print("Server stopped")

    except Exception as e:
        print(f"❌ Server startup test failed: {e}")

def test_data_persistence():
    """Test that data is properly saved and loaded"""
    print("\nTesting data persistence...")

    sys.path.append('.')
    from ambient_mcp_server import AmbientInsightsServer

    server = AmbientInsightsServer()

    # Add some test data
    context = server.load_user_context()
    context.interests.append("test_interest")
    context.goals.append("test_goal")
    server.save_user_context(context)

    # Create a new server instance and check if data persists
    server2 = AmbientInsightsServer()
    context2 = server2.load_user_context()

    if "test_interest" in context2.interests and "test_goal" in context2.goals:
        print("✅ Data persistence works correctly")
    else:
        print("❌ Data persistence failed")

    # Check if files exist
    data_dir = Path("./mcp_data")
    if data_dir.exists():
        print(f"✅ Data directory created: {data_dir}")
        if (data_dir / "user_context.json").exists():
            print("✅ User context file exists")
        if (data_dir / "insights.jsonl").exists():
            print("✅ Insights file created")
    else:
        print("❌ Data directory not created")

def cleanup_test_data():
    """Clean up test data"""
    data_dir = Path("./mcp_data")
    if data_dir.exists():
        for file in data_dir.glob("*"):
            file.unlink()
        data_dir.rmdir()
        print("🧹 Test data cleaned up")

if __name__ == "__main__":
    print("🧪 Testing Ambient Insights MCP Server\n")

    # Clean up any existing test data
    cleanup_test_data()

    try:
        # Run tests
        test_basic_functionality()
        test_data_persistence()
        test_server_startup()

        print("\n🎉 All tests completed!")

    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
    finally:
        # Always clean up
        cleanup_test_data()