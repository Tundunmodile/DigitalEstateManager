"""
CLI Interface for Apex Residences Premium Chatbot
Terminal-based conversation with luxury styling
"""

import os
import logging
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.markdown import Markdown

from .premium_chatbot import PremiumChatbot

logger = logging.getLogger(__name__)

# Luxury color palette
ACCENT_COLOR = "gold1"
PRIMARY_COLOR = "white"
SECONDARY_COLOR = "grey50"
SUCCESS_COLOR = "green"
INFO_COLOR = "cyan"


class CLIInterface:
    """
    Command-line interface for the Premium Chatbot.
    Provides a conversational REPL with luxury styling.
    """

    def __init__(self, chatbot: PremiumChatbot):
        """
        Initialize CLI Interface.

        Args:
            chatbot: PremiumChatbot instance
        """
        self.chatbot = chatbot
        self.console = Console()
        self.running = False

    def print_header(self) -> None:
        """Display welcome banner with luxury styling."""
        header_text = Text(
            "APEX RESIDENCES",
            style=f"bold {ACCENT_COLOR}",
            justify="center"
        )
        subheader = Text(
            "Premium Home Management Concierge",
            style=f"italic {SECONDARY_COLOR}",
            justify="center"
        )

        title_panel = Panel(
            f"{header_text}\n{subheader}",
            style=f"bold {ACCENT_COLOR}",
            padding=(1, 2),
        )
        self.console.print(title_panel)

        info_text = Text(
            "Welcome to your personal concierge. Ask about our services, pricing, team, or anything else. "
            "Type 'help' for commands, 'exit' to quit.",
            style=SECONDARY_COLOR,
            justify="center"
        )
        self.console.print(info_text)
        self.console.print()

    def print_response(self, response_data: dict) -> None:
        """
        Display chatbot response with styling.

        Args:
            response_data: Response dictionary from chatbot
        """
        response_text = response_data.get("response", "")
        source = response_data.get("source", "")

        # Color-coded source badge
        if source == "company":
            badge = "[gold1]🏛[/gold1] Apex Residences"
        else:
            badge = "[grey50]•[/grey50] Response"

        # Panel with response
        panel = Panel(
            response_text,
            title=badge,
            style="bold white",
            border_style=ACCENT_COLOR,
        )
        self.console.print(panel)

    def print_help(self) -> None:
        """Display help information."""
        help_text = """
Available Commands:
  [bold gold1]help[/bold gold1]      - Show this help message
  [bold gold1]clear[/bold gold1]     - Clear conversation history
  [bold gold1]history[/bold gold1]   - Show conversation history
  [bold gold1]exit[/bold gold1]      - Exit the application

Just type your question or message naturally, and I'll provide assistance.
        """
        self.console.print(Markdown(help_text.strip()))

    def handle_command(self, user_input: str) -> bool:
        """
        Handle special commands.

        Args:
            user_input: User input string

        Returns:
            False if should exit, True otherwise
        """
        command = user_input.strip().lower()

        if command == "exit":
            self.console.print(
                Panel(
                    "[gold1]Thank you for using Apex Residences Concierge. Goodbye.[/gold1]",
                    style="bold"
                )
            )
            return False

        elif command == "help":
            self.print_help()
            return True

        elif command == "clear":
            self.chatbot.clear_history()
            self.console.print("[green]✓[/green] Conversation history cleared.")
            return True

        elif command == "history":
            history = self.chatbot.get_history()
            if not history:
                self.console.print("[grey50]No conversation history.[/grey50]")
            else:
                self.console.print("[bold gold1]Conversation History:[/bold gold1]")
                for i, msg in enumerate(history):
                    role = msg["role"].upper()
                    content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                    self.console.print(f"  [{role}] {content}")
            return True

        # Not a command
        return None

    def run(self) -> None:
        """Start interactive CLI conversation loop."""
        self.running = True
        self.print_header()

        try:
            while self.running:
                # Get user input
                try:
                    user_input = Prompt.ask(
                        f"[{ACCENT_COLOR}]You[/{ACCENT_COLOR}]",
                        default="",
                    ).strip()
                except (KeyboardInterrupt, EOFError):
                    self.running = False
                    self.console.print("\n[gold1]Exiting...[/gold1]")
                    break

                if not user_input:
                    continue

                # Check for commands
                command_result = self.handle_command(user_input)
                if command_result is False:
                    self.running = False
                    break
                elif command_result is True:
                    self.console.print()
                    continue

                # Process as normal query
                try:
                    self.console.print("[grey50]Processing your request...[/grey50]")
                    response_data = self.chatbot.get_response(user_input)
                    self.console.print()
                    self.print_response(response_data)
                    self.console.print()

                except Exception as e:
                    logger.error(f"Error processing query: {str(e)}")
                    self.console.print(
                        Panel(
                            f"[red]Error: {str(e)}[/red]",
                            style="bold red",
                        )
                    )
                    self.console.print()

        except KeyboardInterrupt:
            self.console.print("\n[gold1]Thank you. Goodbye.[/gold1]")
        finally:
            self.running = False


def run_cli(
    tavily_api_key: Optional[str] = None
) -> None:
    """
    Launch CLI interface for the chatbot.

    Args:
        tavily_api_key: Tavily API key (uses TAVILY_API_KEY env var if not provided)
    """
    logging.basicConfig(level=logging.INFO)

    try:
        # Initialize chatbot
        chatbot = PremiumChatbot(
            tavily_api_key=tavily_api_key,
        )

        # Run CLI
        cli = CLIInterface(chatbot)
        cli.run()

    except FileNotFoundError as e:
        console = Console()
        console.print(f"[red]Error: {str(e)}[/red]")
        console.print("[yellow]Make sure company_info.md exists in the project root.[/yellow]")
        logger.error(f"File not found: {str(e)}")

    except ValueError as e:
        console = Console()
        console.print(f"[red]Configuration Error: {str(e)}[/red]")
        console.print("[yellow]Check your .env file for required API keys.[/yellow]")
        logger.error(f"Configuration error: {str(e)}")

    except Exception as e:
        console = Console()
        console.print(f"[red]Unexpected Error: {str(e)}[/red]")
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
