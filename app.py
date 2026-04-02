#!/usr/bin/env python3
"""
Apex Residences Premium Chatbot - Main Entry Point
Launches CLI or Web interface for the chatbot
"""

import os
import sys
import argparse
import logging
import warnings
import io
from pathlib import Path

# Suppress HuggingFace Hub messages before any imports
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow logs
os.environ['CUDA_VISIBLE_DEVICES'] = ''  # Avoid GPU warnings

from dotenv import load_dotenv

# Suppress LangChain deprecation warnings (not user-facing)
warnings.filterwarnings('ignore', category=DeprecationWarning, module='langchain')
warnings.filterwarnings('ignore', message='.*HuggingFaceEmbeddings.*')
warnings.filterwarnings('ignore', message='.*unauthenticated requests.*')
warnings.filterwarnings('ignore', category=UserWarning, module='huggingface_hub')
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# Load environment variables
load_dotenv()


# Load .env file if it exists
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Setup logging - suppress verbose initialization messages
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose library logs
logging.getLogger('langchain').setLevel(logging.ERROR)
logging.getLogger('langchain_community').setLevel(logging.ERROR)
logging.getLogger('langchain_huggingface').setLevel(logging.ERROR)
logging.getLogger('transformers').setLevel(logging.ERROR)
logging.getLogger('sentence_transformers').setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.ERROR)
logging.getLogger('openai').setLevel(logging.ERROR)
logging.getLogger('huggingface_hub').setLevel(logging.ERROR)


def print_banner() -> None:
    """Print luxury ASCII banner."""
    banner = """
╔╗ ╔═══╗╔═══╗    ╔══════╗╔═══╗╔═══╗╔════════╗╔═════╗╔════════╔════════╗╔═════╗
║║ ║╔══╝║╔═╗║    ║╔═══╗░║║╔══╝║╔═╗║║╚══╔═══╝║╔═══╣║╔══════╚╔══════╝║╚═══╗║
║╚═╝║   ║║ ║║    ║║   ║░║║║  ║║ ║║║   ║    ║║   //║║        ║        ║    ||
║   ║   ║║ ║║    ║║   ║░║║║  ║║ ║║║   ║    ║║   \\║║        ║        ║    ||
║   ║   ║║ ║║ ╔╗╚║║   ║░║║║  ║║ ║║║   ║    ║║    \║║ ══════╗║ ══════╗║ ═══╣
║   ║╚══╝║╚═╝║║║║╚║╚═══╩╗║╚══╝║╚═╝║║   ║    ║╚═══╗║║╚══════║║╚══════║╚════╗║
╚╝  ╚═══╝╚═══╝╚═╝╚═╚═════╝╚════╝╚═══╝╚═══╝    ╚════╝╚════════╝╚════════╝╚═════╝
                        PREMIUM HOME MANAGEMENT CONCIERGE
                              Luxury Living Redefined
    """
    print(banner)
    print()


def show_menu() -> str:
    """Display launch menu and get user choice."""
    print("Select interface:")
    print("  [1] CLI - Terminal Interface (faster, lean)")
    print("  [2] WEB - Web Browser Interface (luxurious UI)")
    print("  [0] Exit")
    print()
    
    while True:
        choice = input("Enter your choice (0-2): ").strip()
        if choice in ["0", "1", "2"]:
            return choice
        print("Invalid choice. Please enter 0, 1, or 2.")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Apex Residences Premium Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py                 # Show menu
  python app.py --cli           # Launch CLI interface
  python app.py --web           # Launch Web interface
  python app.py --web --port 8000  # Launch Web on custom port
        """,
    )
    
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Launch CLI interface (terminal)"
    )
    
    parser.add_argument(
        "--web",
        action="store_true",
        help="Launch Web interface (browser)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port for Web interface (default: 5000)"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host for Web interface (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode for Web interface"
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Check for Anthropic API key (required for Claude)
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    
    if not anthropic_key:
        print("❌ Error: ANTHROPIC_API_KEY not found in environment variables.")
        print("Please create a .env file with your Anthropic API key:")
        print("ANTHROPIC_API_KEY=your-anthropic-key-here")
        print("\nGet your key from: https://console.anthropic.com/account/keys")
        sys.exit(1)
    
    # Determine which interface to launch
    if args.cli:
        interface = "cli"
    elif args.web:
        interface = "web"
    else:
        # Show menu if no args specified
        choice = show_menu()
        if choice == "0":
            print("Goodbye.")
            sys.exit(0)
        elif choice == "1":
            interface = "cli"
        else:
            interface = "web"
    
    # Launch selected interface
    try:
        if interface == "cli":
            logger.info("Launching CLI interface...")
            print("✓ Using Claude (Anthropic) as LLM\n")
            from chatbot.cli import run_cli
            run_cli(
                tavily_api_key=tavily_api_key
            )
        
        else:  # web
            logger.info(f"Launching Web interface on {args.host}:{args.port}...")
            print(f"\n🌐 Opening browser at http://localhost:{args.port}")
            print("   Press Ctrl+C to stop the server\n")
            
            from chatbot.api import run_app
            run_app(
                host=args.host,
                port=args.port,
                debug=args.debug,
                tavily_api_key=tavily_api_key,
            )
    
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
