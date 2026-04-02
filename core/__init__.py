"""
Core module for Digital Estate Manager
Exports database layer, DAOs, and initialization functions.
"""

from .database import (
    # Initialization
    init_database,
    get_database_stats,
    drop_all_tables,
    
    # Connection management
    get_db_connection,
    
    # Universal CRUD function
    execute_sqlite_query,
    
    # Data Access Objects
    UserDAO,
    AssetDAO,
    CustomerAssetDAO,
    VendorDAO,
    ScheduleDAO,
    EventAuditDAO,
    
    # Data classes
    User,
    Asset,
    Vendor,
    Schedule,
    
    # Database path
    DB_PATH,
)

__all__ = [
    # Initialization
    "init_database",
    "get_database_stats",
    "drop_all_tables",
    
    # Connection
    "get_db_connection",
    
    # Core function
    "execute_sqlite_query",
    
    # DAOs
    "UserDAO",
    "AssetDAO",
    "CustomerAssetDAO",
    "VendorDAO",
    "ScheduleDAO",
    "EventAuditDAO",
    
    # Data classes
    "User",
    "Asset",
    "Vendor",
    "Schedule",
    
    # Database path
    "DB_PATH",
]
