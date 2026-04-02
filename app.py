"""
Digital Estate Manager - Main Application Entry Point
=====================================================

4-Layer Architecture:
- DATA LAYER: SQLite database operations
- AGENT LAYER: LLM orchestration, agents, event bus, tools
- UI LAYER: REST API, WebSocket, session management
- EVAL LAYER: Benchmarks, metrics (future)

This script initializes the application and provides both:
1. CLI mode for testing the orchestrator
2. HTTP API mode for the web interface
"""

import sys
import logging
from pathlib import Path
import argparse
from typing import Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Import data layer
from data_layer import (
    init_database,
    get_database_stats,
    UserDAO,
    AssetDAO,
    VendorDAO,
    CustomerAssetDAO,
    ScheduleDAO,
    DB_PATH,
)

# Import agent layer
from agent_layer.orchestration.orchestrator import Orchestrator

# Import UI layer (optional)
UI_AVAILABLE = True
try:
    from ui_layer.api.main import create_app
except ImportError:
    UI_AVAILABLE = False
    logger.warning("FastAPI not available - API mode disabled")


def display_banner():
    """Display welcome banner with architecture info."""
    banner = """
    ╔════════════════════════════════════════════════════════════╗
    ║     DIGITAL ESTATE MANAGER - LLM ORCHESTRATOR              ║
    ║                                                            ║
    ║  4-Layer Architecture:                                    ║
    ║  ├─ DATA LAYER: SQLite database (users, assets, vendors) ║
    ║  ├─ AGENT LAYER: LLM orchestrator (NL → SQL)             ║
    ║  ├─ UI LAYER: REST API + WebSocket (future)              ║
    ║  └─ EVAL LAYER: Benchmarks & metrics (future)            ║
    ╚════════════════════════════════════════════════════════════╝
    """
    print(banner)


def initialize_app():
    """Initialize the Digital Estate Manager application."""
    logger.info("=" * 70)
    logger.info("INITIALIZING: Digital Estate Manager (Data + Agent Layers)")
    logger.info("=" * 70)
    
    # 1. Initialize database
    try:
        init_database()
        logger.info(f"✓ Data Layer: Database initialized at {DB_PATH}")
    except Exception as e:
        logger.error(f"✗ Failed to initialize database: {e}")
        sys.exit(1)
    
    # 2. Display database statistics
    try:
        stats = get_database_stats()
        logger.info("\n📊 Database Statistics:")
        for table, count in stats.items():
            logger.info(f"   • {table}: {count} rows")
    except Exception as e:
        logger.error(f"Warning: Could not fetch stats: {e}")
    
    # 3. Initialize agent layer (orchestrator)
    try:
        orchestrator = Orchestrator(enable_llm=True)
        logger.info("✓ Agent Layer: LLM Orchestrator initialized")
        logger.info(f"   • LLM: Claude (via Anthropic API)")
        logger.info(f"   • Query Validator: Ready (blocks DELETE/DROP)")
    except Exception as e:
        logger.warning(f"⚠ LLM initialization: {e}")
        orchestrator = Orchestrator(enable_llm=False)
        logger.info("✓ Agent Layer: Template-based orchestrator initialized")
    
    logger.info("\n✓ Application initialized successfully")
    logger.info("=" * 70)
    
    return orchestrator


def demo_crud_operations():
    """Demonstrate basic CRUD operations with the data layer."""
    logger.info("\n" + "=" * 70)
    logger.info("DEMO: Data Layer - CRUD Operations")
    logger.info("=" * 70)
    
    try:
        # 1. Create a user
        logger.info("\n1️⃣  Creating a user...")
        user_id = UserDAO.create(
            username="property_manager",
            password="demo_password",
            email="manager@estateplanner.com"
        )
        logger.info(f"   ✓ User created: ID={user_id}")
        
        # 2. Create assets (properties)
        logger.info("\n2️⃣  Creating assets (properties)...")
        asset1_id = AssetDAO.create(
            property_name="Suburban Family Home",
            address="123 Oak Street, Springfield, IL 62701",
            property_type="house",
            square_footage=3500,
            year_built=1995,
            description="3-bedroom suburban home with large yard"
        )
        logger.info(f"   ✓ Property 1: {asset1_id}")
        
        asset2_id = AssetDAO.create(
            property_name="Downtown Luxury Condo",
            address="456 Main Ave, Chicago, IL 60601",
            property_type="condo",
            square_footage=1800,
            year_built=2015,
            description="Modern 2-bedroom condo in downtown"
        )
        logger.info(f"   ✓ Property 2: {asset2_id}")
        
        # 3. Assign assets to user
        logger.info("\n3️⃣  Assigning assets to user...")
        CustomerAssetDAO.create(user_id, asset1_id, relationship_type="owner")
        CustomerAssetDAO.create(user_id, asset2_id, relationship_type="manager")
        logger.info(f"   ✓ Both properties assigned to user {user_id}")
        
        # 4. Create vendors
        logger.info("\n4️⃣  Creating vendors...")
        vendor1_id = VendorDAO.create(
            vendor_name="Clean Pro Services",
            service_type="cleaning",
            contact_name="Sarah Johnson",
            phone="(555) 123-4567",
            email="sarah@cleanpro.com"
        )
        logger.info(f"   ✓ Cleaning vendor: {vendor1_id}")
        
        vendor2_id = VendorDAO.create(
            vendor_name="Mike's Plumbing",
            service_type="plumbing",
            contact_name="Mike Chen",
            phone="(555) 987-6543",
            email="mike@plumbing.com"
        )
        logger.info(f"   ✓ Plumbing vendor: {vendor2_id}")
        
        # 5. Schedule services
        logger.info("\n5️⃣  Scheduling services...")
        schedule1_id = ScheduleDAO.create(
            asset_id=asset1_id,
            vendor_id=vendor1_id,
            service_type="cleaning",
            scheduled_date="2026-04-10",
            scheduled_time="10:00",
            notes="Biweekly deep clean",
            cost=150.00
        )
        logger.info(f"   ✓ Clean schedule: {schedule1_id}")
        
        schedule2_id = ScheduleDAO.create(
            asset_id=asset2_id,
            vendor_id=vendor2_id,
            service_type="plumbing",
            scheduled_date="2026-04-15",
            scheduled_time="14:00",
            notes="Annual inspection",
            cost=200.00
        )
        logger.info(f"   ✓ Plumbing schedule: {schedule2_id}")
        
        # 6. Retrieve and display
        logger.info("\n6️⃣  Verifying data...")
        user = UserDAO.get_by_id(user_id)
        logger.info(f"   ✓ User: {user['username']} ({user['email']})")
        
        assets = AssetDAO.get_by_user(user_id)
        logger.info(f"   ✓ Managed properties: {len(assets)}")
        for asset in assets:
            logger.info(f"      - {asset['property_name']}")
        
        logger.info("\n✓ Data Layer demo completed successfully\n")
        return user_id, asset1_id
        
    except Exception as e:
        logger.error(f"✗ Data Layer demo failed: {e}", exc_info=True)
        return None, None


def demo_orchestrator(orchestrator: Orchestrator, user_id: Optional[int] = None):
    """Demonstrate the LLM orchestrator layer."""
    logger.info("=" * 70)
    logger.info("DEMO: Agent Layer - LLM Orchestrator")
    logger.info("=" * 70)
    
    # Test queries
    test_queries = [
        "How many properties do I manage?",
        "Show me all vendors",
        "What services are scheduled for the next 30 days?",
        "Get all properties built after 2010",
    ]
    
    logger.info("\nExecuting test queries through the LLM Orchestrator:\n")
    
    for i, query in enumerate(test_queries, 1):
        logger.info(f"{i}. User Query: \"{query}\"")
        
        try:
            result = orchestrator.process_user_input(query, user_id=user_id)
            
            if result["success"]:
                logger.info(f"   ✓ Generated SQL: {result['sql'][:60]}...")
                
                if result.get('results'):
                    result_count = len(result['results']) if isinstance(result['results'], list) else 1
                    logger.info(f"   ✓ Results: {result_count} row(s)")
                    if result_count <= 3 and isinstance(result['results'], list):
                        for row in result['results']:
                            logger.info(f"      - {row}")
                else:
                    logger.info(f"   ✓ Response: {result['message']}")
            else:
                logger.warning(f"   ✗ Error: {result['error']}")
        
        except Exception as e:
            logger.error(f"   ✗ Failed: {e}")
        
        logger.info(f"   🔗 Correlation ID: {result.get('correlation_id', 'N/A')}\n")


def interactive_mode(orchestrator: Orchestrator, user_id: Optional[int] = None):
    """Run interactive CLI mode for testing."""
    logger.info("=" * 70)
    logger.info("INTERACTIVE MODE - Chat with the LLM Orchestrator")
    logger.info("=" * 70)
    logger.info("\nType your queries in natural language. Type 'exit' to quit.\n")
    
    while True:
        try:
            user_input = input("📝 You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                logger.info("\nGoodbye! 👋\n")
                break
            
            if not user_input:
                continue
            
            logger.info("\n🤖 Processing...")
            result = orchestrator.process_user_input(user_input, user_id=user_id)
            
            print("\n" + "=" * 70)
            if result["success"]:
                print(f"✓ Response: {result['message']}")
                if result.get('results'):
                    print(f"\nResults ({len(result['results']) if isinstance(result['results'], list) else 1} row(s)):")
                    if isinstance(result['results'], list) and len(result['results']) <= 5:
                        for i, row in enumerate(result['results'], 1):
                            print(f"  {i}. {row}")
            else:
                print(f"✗ Error: {result['error']}")
            
            print(f"\nSQL: {result.get('sql', 'N/A')}")
            print(f"Correlation ID: {result['correlation_id']}")
            print("=" * 70 + "\n")
        
        except KeyboardInterrupt:
            logger.info("\n\nInterrupted by user. Goodbye! 👋\n")
            break
        except Exception as e:
            logger.error(f"\nError: {e}\n")


def main():
    """Main application entry point."""
    display_banner()
    
    # Initialize the application
    orchestrator = initialize_app()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Digital Estate Manager - LLM Orchestrator")
    parser.add_argument(
        "--mode",
        choices=["demo", "interactive", "both"],
        default="both",
        help="Run mode: demo (test queries), interactive (CLI), or both"
    )
    parser.add_argument(
        "--skip-data-demo",
        action="store_true",
        help="Skip the data layer demo"
    )
    
    args = parser.parse_args()
    
    # Run data layer demo
    if not args.skip_data_demo and args.mode in ["demo", "both"]:
        user_id, asset_id = demo_crud_operations()
    else:
        # Use first user from database if available
        users = UserDAO.get_all()
        user_id = users[0]['id'] if users else None
    
    # Run orchestrator demos
    if args.mode in ["demo", "both"]:
        demo_orchestrator(orchestrator, user_id=user_id)
    
    # Run interactive mode
    if args.mode in ["interactive", "both"]:
        interactive_mode(orchestrator, user_id=user_id)
    
    logger.info("\n✓ Application completed successfully")


if __name__ == "__main__":
    main()