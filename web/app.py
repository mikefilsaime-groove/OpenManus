#!/usr/bin/env python
import asyncio
import json
import os
import sys
import threading
import time
import uuid

from flask import Flask, jsonify, render_template, request, session
from flask_socketio import SocketIO, emit

# Add parent directory to sys.path for imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app.agent.manus import Manus
from app.logger import logger
from app.schema import AgentState

# Get absolute paths for static and templates folders
current_dir = os.path.dirname(os.path.abspath(__file__))
static_folder = os.path.join(current_dir, "static")
template_folder = os.path.join(current_dir, "templates")

# Initialize Flask app
app = Flask(__name__, static_folder=static_folder, template_folder=template_folder)
app.secret_key = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*")

# Track active agent sessions
active_agents = {}


class AgentRunner:
    def __init__(self, session_id):
        self.session_id = session_id
        self.agent = Manus()
        self.output_buffer = []
        self.is_running = False
        self.step_count = 0
        self.state = "idle"

    async def run_agent(self, prompt):
        self.is_running = True
        self.state = "running"

        try:
            # Override the logger to capture output for the web UI
            original_info = logger.info
            original_warning = logger.warning

            def custom_logger(msg):
                self.output_buffer.append({"type": "log", "content": str(msg)})
                socketio.emit(
                    "agent_update",
                    {"log": str(msg), "session_id": self.session_id},
                    namespace="/manus",
                )
                original_info(msg)

            logger.info = custom_logger
            logger.warning = custom_logger

            # Run the agent
            await self.agent.run(prompt)

            # Restore original loggers
            logger.info = original_info
            logger.warning = original_warning

            self.state = "completed"
        except Exception as e:
            self.output_buffer.append({"type": "error", "content": str(e)})
            socketio.emit(
                "agent_update",
                {"error": str(e), "session_id": self.session_id},
                namespace="/manus",
            )
            self.state = "error"
        finally:
            self.is_running = False
            socketio.emit(
                "agent_complete",
                {"session_id": self.session_id, "state": self.state},
                namespace="/manus",
            )


def run_agent_thread(session_id, prompt):
    """Run agent in a separate thread using asyncio"""
    agent_runner = active_agents[session_id]

    async def run():
        await agent_runner.run_agent(prompt)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run())
    loop.close()


@app.route("/")
def index():
    """Render the main interface"""
    # Create a unique session ID for this user
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())

    return render_template("index.html", session_id=session["session_id"])


@app.route("/api/run", methods=["POST"])
def run_manus():
    """API endpoint to run Manus agent"""
    data = request.json
    prompt = data.get("prompt", "")
    session_id = data.get("session_id")

    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    if not session_id:
        return jsonify({"error": "No session ID provided"}), 400

    # Create a new agent runner for this session if it doesn't exist
    if session_id not in active_agents:
        active_agents[session_id] = AgentRunner(session_id)

    agent_runner = active_agents[session_id]

    # Check if agent is already running
    if agent_runner.is_running:
        return jsonify({"error": "Agent is already running"}), 409

    # Start the agent in a new thread
    thread = threading.Thread(target=run_agent_thread, args=(session_id, prompt))
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started", "session_id": session_id})


@app.route("/api/status/<session_id>", methods=["GET"])
def get_status(session_id):
    """Get the status of a running agent"""
    if session_id not in active_agents:
        return jsonify({"error": "Session not found"}), 404

    agent_runner = active_agents[session_id]

    return jsonify(
        {
            "is_running": agent_runner.is_running,
            "state": agent_runner.state,
            "step_count": agent_runner.step_count,
            "output": agent_runner.output_buffer,
        }
    )


@socketio.on("connect", namespace="/manus")
def socket_connect():
    """Handle WebSocket connection"""
    emit("connected", {"status": "connected"})


@socketio.on("disconnect", namespace="/manus")
def socket_disconnect():
    """Handle WebSocket disconnection"""
    # Cleanup if needed
    pass


# Clean up old sessions periodically
def cleanup_sessions():
    """Remove inactive sessions after a period of time"""
    while True:
        time.sleep(3600)  # Check every hour
        # Implementation of cleanup logic


if __name__ == "__main__":
    # Start the cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_sessions)
    cleanup_thread.daemon = True
    cleanup_thread.start()

    # Start the Flask application
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
