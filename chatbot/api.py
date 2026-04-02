"""
Flask REST API for Apex Residences Premium Chatbot
Provides web interface endpoints
"""

import os
import logging
from typing import Optional
from functools import wraps

from flask import Flask, request, jsonify
from flask_cors import CORS

from .premium_chatbot import PremiumChatbot

logger = logging.getLogger(__name__)


def create_app(
    tavily_api_key: Optional[str] = None,
) -> Flask:
    """
    Create and configure Flask application.

    Args:
        tavily_api_key: Tavily API key

    Returns:
        Configured Flask app instance
    """
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
        static_url_path="/static",
    )

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize chatbot
    try:
        chatbot = PremiumChatbot(
            tavily_api_key=tavily_api_key,
        )
        logger.info("Chatbot initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize chatbot: {str(e)}")
        chatbot = None

    def require_chatbot(f):
        """Decorator to check if chatbot is available."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if chatbot is None:
                return jsonify({"error": "Chatbot not initialized"}), 500
            return f(*args, **kwargs)
        return decorated_function

    # Routes

    @app.route("/", methods=["GET"])
    def index():
        """Serve main HTML page."""
        return app.send_static_file("index.html")

    @app.route("/api/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({
            "status": "healthy",
            "service": "Apex Residences Chatbot",
            "version": "1.0.0",
        })

    @app.route("/api/chat", methods=["POST"])
    @require_chatbot
    def chat():
        """
        Chat endpoint.
        
        Request JSON:
        {
            "message": "User query string",
            "include_source": true/false (optional, default true)
        }
        
        Response JSON:
        {
            "response": "Chatbot response text",
            "source": "company|web",
            "timestamp": "ISO timestamp"
        }
        """
        try:
            data = request.get_json(force=True)

            if not data or "message" not in data:
                return jsonify({"error": "Missing 'message' in request body"}), 400

            user_message = data.get("message", "").strip()

            if not user_message:
                return jsonify({"error": "Message cannot be empty"}), 400

            # Check message length
            if len(user_message) > 5000:
                return jsonify({"error": "Message too long (max 5000 characters)"}), 400

            # Get response
            include_source = data.get("include_source", True)
            response_data = chatbot.get_response(user_message, include_source=include_source)

            return jsonify(response_data), 200

        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return jsonify({"error": f"Validation error: {str(e)}"}), 400

        except Exception as e:
            logger.error(f"Chat endpoint error: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/history", methods=["GET"])
    @require_chatbot
    def get_history():
        """Get conversation history."""
        try:
            history = chatbot.get_history()
            return jsonify({"history": history}), 200
        except Exception as e:
            logger.error(f"History endpoint error: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/history", methods=["DELETE"])
    @require_chatbot
    def clear_history():
        """Clear conversation history."""
        try:
            chatbot.clear_history()
            return jsonify({"message": "History cleared"}), 200
        except Exception as e:
            logger.error(f"Clear history endpoint error: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/status", methods=["GET"])
    @require_chatbot
    def get_status():
        """Get chatbot and system status including circuit breaker states."""
        try:
            status = {
                "service": "Apex Residences Chatbot",
                "status": "healthy",
                "conversation_id": chatbot.conversation_id,
                "persistence_enabled": chatbot.enable_persistence,
                "tools_enabled": chatbot.tool_manager is not None,
                "circuit_breakers": {
                    "anthropic_api": chatbot.anthropic_breaker.get_status(),
                    "tavily_api": chatbot.tavily_breaker.get_status(),
                }
            }
            return jsonify(status), 200
        except Exception as e:
            logger.error(f"Status endpoint error: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route("/api/tools", methods=["GET"])
    @require_chatbot
    def get_tools():
        """Get available tools."""
        try:
            if not chatbot.tool_manager:
                return jsonify({"tools": [], "message": "Tools not available"}), 200
            
            tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                } for tool in chatbot.tool_manager.tools.values()
            ]
            return jsonify({"tools": tools, "count": len(tools)}), 200
        except Exception as e:
            logger.error(f"Tools endpoint error: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger.error(f"Internal error: {str(error)}")
        return jsonify({"error": "Internal server error"}), 500

    return app


def run_app(
    host: str = "0.0.0.0",
    port: int = 5000,
    debug: bool = False,
    tavily_api_key: Optional[str] = None,
) -> None:
    """
    Run Flask application.

    Args:
        host: Host to bind to
        port: Port to bind to
        debug: Enable debug mode
        tavily_api_key: Tavily API key
    """
    logging.basicConfig(level=logging.INFO)

    app = create_app(tavily_api_key=tavily_api_key)

    logger.info(f"Starting server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
