"""
Data Layer for Digital Estate Manager
======================================
Handles all database operations for:
- Users, Assets (Properties), Customer-Asset relationships
- Vendors, Service Schedules, Audit trails

Core components:
1. Database schema initialization
2. execute_sqlite_query() - Universal CRUD function
3. DAO classes - Data Access Objects for each entity
4. Connection management with proper cleanup
"""

import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional, List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Database file location (2 levels up to project root, then data/)
DB_PATH = Path(__file__).parent.parent / "data" / "estate_manager.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# ============================================================================
# SCHEMA DEFINITIONS
# ============================================================================

SCHEMA_SQL = """
-- Users table: Store single primary user + future multi-user support
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assets table: Properties managed by the company
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_name TEXT NOT NULL,
    address TEXT NOT NULL UNIQUE,
    property_type TEXT NOT NULL,  -- house, condo, apartment, commercial
    square_footage INTEGER,
    year_built INTEGER,
    description TEXT,
    status TEXT DEFAULT 'active',  -- active, inactive, archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer-Assets join table: Maps users to their managed properties
CREATE TABLE IF NOT EXISTS customer_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    asset_id INTEGER NOT NULL,
    relationship_type TEXT NOT NULL,  -- owner, manager, tenant
    assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
    UNIQUE(user_id, asset_id)
);

-- Vendors table: Service providers and their information
CREATE TABLE IF NOT EXISTS vendors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_name TEXT NOT NULL,
    service_type TEXT NOT NULL,  -- cleaning, maintenance, plumbing, electrical, landscaping, etc
    contact_name TEXT,
    phone TEXT,
    email TEXT,
    rating REAL DEFAULT 0.0,  -- 1-5 star rating
    notes TEXT,
    status TEXT DEFAULT 'active',  -- active, inactive
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Schedules table: Historical + future service logs
CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    vendor_id INTEGER NOT NULL,
    service_type TEXT NOT NULL,
    scheduled_date DATE NOT NULL,
    scheduled_time TIME,
    completion_date TIMESTAMP,  -- NULL if not completed yet
    status TEXT DEFAULT 'scheduled',  -- scheduled, in_progress, completed, cancelled
    notes TEXT,
    cost REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE SET NULL
);

-- Event audit trail: Log critical operations for debugging + compliance
CREATE TABLE IF NOT EXISTS event_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,  -- USER_INPUT_RECEIVED, TASK_EXTRACTED, OPERATION_COMPLETED, etc
    source TEXT,
    data TEXT,  -- JSON string
    correlation_id TEXT,  -- For tracing across loops
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_customer_assets_user_id ON customer_assets(user_id);
CREATE INDEX IF NOT EXISTS idx_customer_assets_asset_id ON customer_assets(asset_id);
CREATE INDEX IF NOT EXISTS idx_schedules_asset_id ON schedules(asset_id);
CREATE INDEX IF NOT EXISTS idx_schedules_vendor_id ON schedules(vendor_id);
CREATE INDEX IF NOT EXISTS idx_schedules_date ON schedules(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_event_audit_type ON event_audit(event_type);
CREATE INDEX IF NOT EXISTS idx_event_audit_correlation ON event_audit(correlation_id);
"""


# ============================================================================
# CONNECTION MANAGEMENT
# ============================================================================

@contextmanager
def get_db_connection():
    """
    Context manager for SQLite database connections.
    
    Ensures proper connection cleanup and enables foreign keys.
    
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


# ============================================================================
# UNIVERSAL CRUD FUNCTION
# ============================================================================

def execute_sqlite_query(
    query: str,
    params: Tuple = (),
    operation_type: str = "SELECT",
    fetch: str = "all"
) -> Any:
    """
    Universal CRUD function for all database operations.
    
    Handles SELECT, INSERT, UPDATE, DELETE with parameterized queries
    to prevent SQL injection. Supports multiple fetch modes.
    
    Args:
        query (str): SQL query with ? placeholders for parameters
        params (tuple): Parameters to bind to query (default: empty)
        operation_type (str): "SELECT", "INSERT", "UPDATE", "DELETE" (for logging)
        fetch (str): Return mode:
            - "all": List of all rows as dicts
            - "one": Single row as dict or None
            - "count": Number of affected rows (int)
            - "lastid": Last inserted row ID (int)
    
    Returns:
        Varies by fetch mode (list, dict, int, or None)
    
    Raises:
        sqlite3.Error: Database operation failed
    
    Examples:
        # INSERT
        user_id = execute_sqlite_query(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            ("john", "secret", "john@example.com"),
            operation_type="INSERT",
            fetch="lastid"
        )
        
        # SELECT all
        users = execute_sqlite_query(
            "SELECT * FROM users WHERE status = ?",
            ("active",),
            operation_type="SELECT",
            fetch="all"
        )
        
        # UPDATE
        rows_affected = execute_sqlite_query(
            "UPDATE users SET email = ? WHERE id = ?",
            ("new@example.com", 1),
            operation_type="UPDATE",
            fetch="count"
        )
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            # Return based on fetch mode
            if fetch == "one":
                row = cursor.fetchone()
                return dict(row) if row else None
            elif fetch == "all":
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            elif fetch == "count":
                return cursor.rowcount
            elif fetch == "lastid":
                return cursor.lastrowid
            else:
                raise ValueError(f"Invalid fetch mode: {fetch}")
    
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity constraint violation: {e}")
        raise
    except sqlite3.Error as e:
        logger.error(f"Database operation failed ({operation_type}): {e}")
        raise


# ============================================================================
# DATACLASSES FOR TYPE SAFETY
# ============================================================================

@dataclass
class User:
    """Represents a user in the system."""
    id: int
    username: str
    password: str
    email: str
    created_at: str
    updated_at: str


@dataclass
class Asset:
    """Represents a property/asset managed by the company."""
    id: int
    property_name: str
    address: str
    property_type: str
    square_footage: Optional[int]
    year_built: Optional[int]
    description: Optional[str]
    status: str
    created_at: str
    updated_at: str


@dataclass
class Vendor:
    """Represents a service vendor."""
    id: int
    vendor_name: str
    service_type: str
    contact_name: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    rating: float
    notes: Optional[str]
    status: str
    created_at: str
    updated_at: str


@dataclass
class Schedule:
    """Represents a service schedule entry."""
    id: int
    asset_id: int
    vendor_id: int
    service_type: str
    scheduled_date: str
    scheduled_time: Optional[str]
    completion_date: Optional[str]
    status: str
    notes: Optional[str]
    cost: Optional[float]
    created_at: str
    updated_at: str


# ============================================================================
# DATA ACCESS OBJECTS (DAO)
# ============================================================================

class UserDAO:
    """Data Access Object for user operations."""
    
    @staticmethod
    def create(username: str, password: str, email: str) -> int:
        """Create a new user. Returns user ID."""
        return execute_sqlite_query(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            (username, password, email),
            operation_type="INSERT",
            fetch="lastid"
        )
    
    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict]:
        """Retrieve user by ID."""
        return execute_sqlite_query(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
            operation_type="SELECT",
            fetch="one"
        )
    
    @staticmethod
    def get_by_username(username: str) -> Optional[Dict]:
        """Retrieve user by username (for login)."""
        return execute_sqlite_query(
            "SELECT * FROM users WHERE username = ?",
            (username,),
            operation_type="SELECT",
            fetch="one"
        )
    
    @staticmethod
    def get_all() -> List[Dict]:
        """Retrieve all users."""
        return execute_sqlite_query(
            "SELECT * FROM users ORDER BY created_at DESC",
            operation_type="SELECT",
            fetch="all"
        )
    
    @staticmethod
    def update(user_id: int, **kwargs) -> int:
        """Update user fields. Returns rows affected."""
        # Build dynamic UPDATE query
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [user_id]
        
        return execute_sqlite_query(
            f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            tuple(values),
            operation_type="UPDATE",
            fetch="count"
        )
    
    @staticmethod
    def delete(user_id: int) -> int:
        """Delete user. Returns rows affected."""
        return execute_sqlite_query(
            "DELETE FROM users WHERE id = ?",
            (user_id,),
            operation_type="DELETE",
            fetch="count"
        )


class AssetDAO:
    """Data Access Object for asset (property) operations."""
    
    @staticmethod
    def create(property_name: str, address: str, property_type: str,
               square_footage: Optional[int] = None, year_built: Optional[int] = None,
               description: Optional[str] = None) -> int:
        """Create a new asset. Returns asset ID."""
        return execute_sqlite_query(
            """INSERT INTO assets (property_name, address, property_type, 
                                   square_footage, year_built, description)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (property_name, address, property_type, square_footage, year_built, description),
            operation_type="INSERT",
            fetch="lastid"
        )
    
    @staticmethod
    def get_by_id(asset_id: int) -> Optional[Dict]:
        """Retrieve asset by ID."""
        return execute_sqlite_query(
            "SELECT * FROM assets WHERE id = ?",
            (asset_id,),
            operation_type="SELECT",
            fetch="one"
        )
    
    @staticmethod
    def get_all() -> List[Dict]:
        """Retrieve all assets."""
        return execute_sqlite_query(
            "SELECT * FROM assets ORDER BY created_at DESC",
            operation_type="SELECT",
            fetch="all"
        )
    
    @staticmethod
    def get_by_user(user_id: int) -> List[Dict]:
        """Retrieve all assets assigned to a user."""
        return execute_sqlite_query(
            """SELECT a.* FROM assets a
               JOIN customer_assets ca ON a.id = ca.asset_id
               WHERE ca.user_id = ? AND a.status = 'active'
               ORDER BY a.property_name""",
            (user_id,),
            operation_type="SELECT",
            fetch="all"
        )
    
    @staticmethod
    def update(asset_id: int, **kwargs) -> int:
        """Update asset fields. Returns rows affected."""
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [asset_id]
        
        return execute_sqlite_query(
            f"UPDATE assets SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            tuple(values),
            operation_type="UPDATE",
            fetch="count"
        )
    
    @staticmethod
    def delete(asset_id: int) -> int:
        """Delete asset. Returns rows affected."""
        return execute_sqlite_query(
            "DELETE FROM assets WHERE id = ?",
            (asset_id,),
            operation_type="DELETE",
            fetch="count"
        )


class CustomerAssetDAO:
    """Data Access Object for user-asset relationships."""
    
    @staticmethod
    def create(user_id: int, asset_id: int, relationship_type: str = "owner") -> int:
        """Associate a user with an asset. Returns relationship ID."""
        return execute_sqlite_query(
            "INSERT INTO customer_assets (user_id, asset_id, relationship_type) VALUES (?, ?, ?)",
            (user_id, asset_id, relationship_type),
            operation_type="INSERT",
            fetch="lastid"
        )
    
    @staticmethod
    def get_all_for_user(user_id: int) -> List[Dict]:
        """Get all asset assignments for a user."""
        return execute_sqlite_query(
            "SELECT * FROM customer_assets WHERE user_id = ? ORDER BY assigned_date DESC",
            (user_id,),
            operation_type="SELECT",
            fetch="all"
        )
    
    @staticmethod
    def get_all_for_asset(asset_id: int) -> List[Dict]:
        """Get all user assignments for an asset."""
        return execute_sqlite_query(
            "SELECT * FROM customer_assets WHERE asset_id = ?",
            (asset_id,),
            operation_type="SELECT",
            fetch="all"
        )
    
    @staticmethod
    def delete(user_id: int, asset_id: int) -> int:
        """Remove asset assignment from user. Returns rows affected."""
        return execute_sqlite_query(
            "DELETE FROM customer_assets WHERE user_id = ? AND asset_id = ?",
            (user_id, asset_id),
            operation_type="DELETE",
            fetch="count"
        )


class VendorDAO:
    """Data Access Object for vendor operations."""
    
    @staticmethod
    def create(vendor_name: str, service_type: str, contact_name: Optional[str] = None,
               phone: Optional[str] = None, email: Optional[str] = None,
               notes: Optional[str] = None) -> int:
        """Create a new vendor. Returns vendor ID."""
        return execute_sqlite_query(
            """INSERT INTO vendors (vendor_name, service_type, contact_name, phone, email, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (vendor_name, service_type, contact_name, phone, email, notes),
            operation_type="INSERT",
            fetch="lastid"
        )
    
    @staticmethod
    def get_by_id(vendor_id: int) -> Optional[Dict]:
        """Retrieve vendor by ID."""
        return execute_sqlite_query(
            "SELECT * FROM vendors WHERE id = ?",
            (vendor_id,),
            operation_type="SELECT",
            fetch="one"
        )
    
    @staticmethod
    def get_all() -> List[Dict]:
        """Retrieve all vendors."""
        return execute_sqlite_query(
            "SELECT * FROM vendors WHERE status = 'active' ORDER BY vendor_name",
            operation_type="SELECT",
            fetch="all"
        )
    
    @staticmethod
    def get_by_service_type(service_type: str) -> List[Dict]:
        """Retrieve all vendors offering a specific service."""
        return execute_sqlite_query(
            "SELECT * FROM vendors WHERE service_type = ? AND status = 'active' ORDER BY rating DESC",
            (service_type,),
            operation_type="SELECT",
            fetch="all"
        )
    
    @staticmethod
    def update(vendor_id: int, **kwargs) -> int:
        """Update vendor fields. Returns rows affected."""
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [vendor_id]
        
        return execute_sqlite_query(
            f"UPDATE vendors SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            tuple(values),
            operation_type="UPDATE",
            fetch="count"
        )
    
    @staticmethod
    def delete(vendor_id: int) -> int:
        """Delete vendor (soft delete via status). Returns rows affected."""
        return execute_sqlite_query(
            "UPDATE vendors SET status = 'inactive', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (vendor_id,),
            operation_type="UPDATE",
            fetch="count"
        )


class ScheduleDAO:
    """Data Access Object for schedule operations."""
    
    @staticmethod
    def create(asset_id: int, vendor_id: int, service_type: str,
               scheduled_date: str, scheduled_time: Optional[str] = None,
               notes: Optional[str] = None, cost: Optional[float] = None) -> int:
        """Create a new schedule entry. Returns schedule ID."""
        return execute_sqlite_query(
            """INSERT INTO schedules (asset_id, vendor_id, service_type, scheduled_date, 
                                     scheduled_time, notes, cost)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (asset_id, vendor_id, service_type, scheduled_date, scheduled_time, notes, cost),
            operation_type="INSERT",
            fetch="lastid"
        )
    
    @staticmethod
    def get_by_id(schedule_id: int) -> Optional[Dict]:
        """Retrieve schedule entry by ID."""
        return execute_sqlite_query(
            "SELECT * FROM schedules WHERE id = ?",
            (schedule_id,),
            operation_type="SELECT",
            fetch="one"
        )
    
    @staticmethod
    def get_all_for_asset(asset_id: int, include_completed: bool = True) -> List[Dict]:
        """Retrieve all schedules for an asset."""
        status_filter = "" if include_completed else "AND status != 'completed'"
        return execute_sqlite_query(
            f"""SELECT * FROM schedules 
               WHERE asset_id = ? {status_filter}
               ORDER BY scheduled_date ASC, scheduled_time ASC""",
            (asset_id,),
            operation_type="SELECT",
            fetch="all"
        )
    
    @staticmethod
    def get_upcoming(asset_id: int, days_ahead: int = 30) -> List[Dict]:
        """Get upcoming schedules for an asset (next N days)."""
        return execute_sqlite_query(
            """SELECT * FROM schedules 
               WHERE asset_id = ? 
               AND scheduled_date BETWEEN DATE('now') AND DATE('now', '+' || ? || ' days')
               AND status IN ('scheduled', 'in_progress')
               ORDER BY scheduled_date ASC, scheduled_time ASC""",
            (asset_id, days_ahead),
            operation_type="SELECT",
            fetch="all"
        )
    
    @staticmethod
    def update(schedule_id: int, **kwargs) -> int:
        """Update schedule fields. Returns rows affected."""
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [schedule_id]
        
        return execute_sqlite_query(
            f"UPDATE schedules SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            tuple(values),
            operation_type="UPDATE",
            fetch="count"
        )
    
    @staticmethod
    def mark_completed(schedule_id: int, completion_date: Optional[str] = None) -> int:
        """Mark a schedule as completed. Returns rows affected."""
        completion_date = completion_date or datetime.now().isoformat()
        return execute_sqlite_query(
            """UPDATE schedules 
               SET status = 'completed', completion_date = ?, updated_at = CURRENT_TIMESTAMP 
               WHERE id = ?""",
            (completion_date, schedule_id),
            operation_type="UPDATE",
            fetch="count"
        )


class EventAuditDAO:
    """Data Access Object for event audit trail."""
    
    @staticmethod
    def log_event(event_type: str, source: str, data: str,
                  correlation_id: Optional[str] = None) -> int:
        """Log an event to audit trail. Returns log ID."""
        return execute_sqlite_query(
            """INSERT INTO event_audit (event_type, source, data, correlation_id)
               VALUES (?, ?, ?, ?)""",
            (event_type, source, data, correlation_id),
            operation_type="INSERT",
            fetch="lastid"
        )
    
    @staticmethod
    def get_by_correlation_id(correlation_id: str) -> List[Dict]:
        """Retrieve all events with a specific correlation ID (for tracing)."""
        return execute_sqlite_query(
            "SELECT * FROM event_audit WHERE correlation_id = ? ORDER BY timestamp ASC",
            (correlation_id,),
            operation_type="SELECT",
            fetch="all"
        )
    
    @staticmethod
    def get_by_type(event_type: str, limit: int = 100) -> List[Dict]:
        """Retrieve recent events of a specific type."""
        return execute_sqlite_query(
            """SELECT * FROM event_audit 
               WHERE event_type = ? 
               ORDER BY timestamp DESC 
               LIMIT ?""",
            (event_type, limit),
            operation_type="SELECT",
            fetch="all"
        )


# ============================================================================
# DATABASE INITIALIZATION & MAINTENANCE
# ============================================================================

def init_database():
    """Initialize database schema. Safe to call multiple times (uses IF NOT EXISTS)."""
    try:
        with get_db_connection() as conn:
            conn.executescript(SCHEMA_SQL)
            logger.info(f"✓ Database initialized at {DB_PATH}")
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def get_database_stats() -> Dict[str, int]:
    """Get basic statistics about database contents."""
    stats = {}
    tables = ['users', 'assets', 'vendors', 'schedules', 'customer_assets', 'event_audit']
    
    for table in tables:
        count = execute_sqlite_query(
            f"SELECT COUNT(*) as count FROM {table}",
            operation_type="SELECT",
            fetch="one"
        )
        stats[table] = count['count'] if count else 0
    
    return stats


def drop_all_tables():
    """
    Drop all tables. USE WITH CAUTION - Development/testing only!
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            # Drop all tables
            tables = ['event_audit', 'schedules', 'customer_assets', 'vendors', 'assets', 'users']
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
            
            cursor.execute("PRAGMA foreign_keys = ON")
            logger.warning("✓ All tables dropped")
    except sqlite3.Error as e:
        logger.error(f"Failed to drop tables: {e}")
        raise
