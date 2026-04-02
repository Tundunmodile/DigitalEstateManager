"""
QUICK START GUIDE - Data Layer Operations
==========================================

Copy-paste ready code snippets for common operations.
"""

# ============================================================================
# IMPORTS (Add to your file)
# ============================================================================

from core import (
    init_database,
    get_database_stats,
    execute_sqlite_query,
    UserDAO,
    AssetDAO,
    CustomerAssetDAO,
    VendorDAO,
    ScheduleDAO,
    EventAuditDAO,
)
import json


# ============================================================================
# 1. INITIALIZATION (Call once on app startup)
# ============================================================================

def setup():
    """Initialize the database on app startup."""
    init_database()  # Creates tables if they don't exist
    print(get_database_stats())  # Show what's in database


# ============================================================================
# 2. USER MANAGEMENT
# ============================================================================

# Create a user
user_id = UserDAO.create(
    username="john_doe",
    password="secure_password",  # TODO: Hash this!
    email="john@example.com"
)

# Get user by ID
user = UserDAO.get_by_id(user_id)
print(f"User: {user['username']} ({user['email']})")

# Get user by username (for login)
user = UserDAO.get_by_username("john_doe")

# Update user
UserDAO.update(user_id, email="newemail@example.com")

# List all users
all_users = UserDAO.get_all()


# ============================================================================
# 3. PROPERTY/ASSET MANAGEMENT
# ============================================================================

# Create a property
asset_id = AssetDAO.create(
    property_name="Mountain Cabin",
    address="789 Pine Road, Boulder, CO",
    property_type="house",
    square_footage=2500,
    year_built=2005,
    description="Cozy cabin with mountain views"
)

# Get property by ID
property = AssetDAO.get_by_id(asset_id)

# Get all properties
all_properties = AssetDAO.get_all()

# Get all properties for a specific user
user_properties = AssetDAO.get_by_user(user_id)

# Update property
AssetDAO.update(asset_id, status="inactive")


# ============================================================================
# 4. ASSIGN PROPERTIES TO USERS
# ============================================================================

# Link user to property
rel_id = CustomerAssetDAO.create(
    user_id=user_id,
    asset_id=asset_id,
    relationship_type="owner"  # owner, manager, or tenant
)

# Get all properties managed by user
user_assets = AssetDAO.get_by_user(user_id)

# Get all users managing a property
managers = CustomerAssetDAO.get_all_for_asset(asset_id)

# Unassign property from user
CustomerAssetDAO.delete(user_id, asset_id)


# ============================================================================
# 5. VENDOR MANAGEMENT
# ============================================================================

# Create a vendor
vendor_id = VendorDAO.create(
    vendor_name="Mountain Maintenance Co",
    service_type="maintenance",
    contact_name="Bob Smith",
    phone="(720) 555-1234",
    email="bob@mountainmaint.com",
    notes="Reliable and thorough"
)

# Get vendor by ID
vendor = VendorDAO.get_by_id(vendor_id)

# Get vendor by service type (e.g., all cleaners)
cleaners = VendorDAO.get_by_service_type("cleaning")

# Update vendor rating
VendorDAO.update(vendor_id, rating=4.8)

# Inactive vendor (soft delete)
VendorDAO.delete(vendor_id)  # Sets status='inactive'


# ============================================================================
# 6. SCHEDULING SERVICES
# ============================================================================

# Schedule a service
schedule_id = ScheduleDAO.create(
    asset_id=asset_id,
    vendor_id=vendor_id,
    service_type="maintenance",
    scheduled_date="2026-04-15",
    scheduled_time="10:00",
    notes="Spring maintenance inspection",
    cost=250.00
)

# Get schedule by ID
schedule = ScheduleDAO.get_by_id(schedule_id)

# Get all schedules for a property
schedules = ScheduleDAO.get_all_for_asset(asset_id)

# Get upcoming schedules (next 30 days)
upcoming = ScheduleDAO.get_upcoming(asset_id, days_ahead=30)

# Update schedule status
ScheduleDAO.update(schedule_id, status="in_progress")

# Mark service as completed
ScheduleDAO.mark_completed(schedule_id)  # completion_date set to now

# Cancel a service
ScheduleDAO.update(schedule_id, status="cancelled")


# ============================================================================
# 7. AUDIT TRAIL / EVENT LOGGING
# ============================================================================

# Log an event
event_id = EventAuditDAO.log_event(
    event_type="SCHEDULE_CREATED",
    source="ChatBot",
    data=json.dumps({"schedule_id": 42, "vendor": "Bob"}),
    correlation_id="user-session-123"  # For tracing across loops
)

# Retrieve all events with same correlation ID (trace user action)
events = EventAuditDAO.get_by_correlation_id("user-session-123")
for event in events:
    print(f"{event['event_type']} at {event['timestamp']}")

# Get recent events of specific type
recent_schedules = EventAuditDAO.get_by_type("SCHEDULE_CREATED", limit=10)


# ============================================================================
# 8. DIRECT SQL (When DAOs aren't enough)
# ============================================================================

# SELECT all vendors with rating > 4.0
high_rated = execute_sqlite_query(
    "SELECT * FROM vendors WHERE rating > ? ORDER BY rating DESC",
    (4.0,),
    operation_type="SELECT",
    fetch="all"
)

# COUNT completed schedules for an asset
count = execute_sqlite_query(
    "SELECT COUNT(*) as total FROM schedules WHERE asset_id = ? AND status = 'completed'",
    (asset_id,),
    operation_type="SELECT",
    fetch="one"
)
print(f"Completed services: {count['total']}")

# UPDATE multiple schedules
rows_updated = execute_sqlite_query(
    "UPDATE schedules SET status = 'completed' WHERE asset_id = ? AND scheduled_date < DATE('now')",
    (asset_id,),
    operation_type="UPDATE",
    fetch="count"
)

# DELETE old scheduled entries
rows_deleted = execute_sqlite_query(
    "DELETE FROM schedules WHERE status = 'cancelled' AND scheduled_date < DATE('now', '-30 days')",
    (),
    operation_type="DELETE",
    fetch="count"
)


# ============================================================================
# 9. COMMON PATTERNS
# ============================================================================

# Pattern 1: Get all services for a user's properties
def get_user_services(user_id):
    """Return upcoming services for all user's properties."""
    user_assets = AssetDAO.get_by_user(user_id)
    all_services = []
    
    for asset in user_assets:
        services = ScheduleDAO.get_upcoming(asset['id'])
        all_services.extend(services)
    
    return all_services


# Pattern 2: Create a complete schedule (property + vendor + service)
def schedule_service(user_id, asset_name, vendor_name, service_type, date, time):
    """Schedule a service for one of user's properties."""
    # Find the asset by name
    assets = execute_sqlite_query(
        "SELECT id FROM assets WHERE property_name = ? AND status = 'active'",
        (asset_name,),
        fetch="one"
    )
    if not assets:
        raise ValueError(f"Property '{asset_name}' not found")
    
    asset_id = assets['id']
    
    # Find vendor by service type
    vendors = VendorDAO.get_by_service_type(service_type)
    if not vendors:
        raise ValueError(f"No vendors found for '{service_type}'")
    
    vendor_id = vendors[0]['id']  # Get first (highest rated)
    
    # Create schedule
    schedule_id = ScheduleDAO.create(
        asset_id=asset_id,
        vendor_id=vendor_id,
        service_type=service_type,
        scheduled_date=date,
        scheduled_time=time
    )
    
    return schedule_id


# Pattern 3: Generate property status report
def get_property_summary(user_id):
    """Generate summary of all user's properties and upcoming services."""
    summary = {}
    
    for asset in AssetDAO.get_by_user(user_id):
        upcoming = ScheduleDAO.get_upcoming(asset['id'], days_ahead=30)
        summary[asset['property_name']] = {
            'type': asset['property_type'],
            'address': asset['address'],
            'upcoming_services': len(upcoming),
            'next_service': upcoming[0]['scheduled_date'] if upcoming else None
        }
    
    return summary


# Pattern 4: Log operation with correlation ID (for EventBus integration)
def log_operation(event_type, operation_data, correlation_id):
    """Log an operation for audit trail + debugging."""
    EventAuditDAO.log_event(
        event_type=event_type,
        source="ApplicationLogic",
        data=json.dumps(operation_data),
        correlation_id=correlation_id
    )


# ============================================================================
# 10. ERROR HANDLING
# ============================================================================

try:
    # Try to create user with duplicate username
    UserDAO.create("john_doe", "pass", "john@example.com")
except Exception as e:
    print(f"Error: {e}")  # "UNIQUE constraint failed: users.username"

try:
    # Try to assign property that doesn't exist
    CustomerAssetDAO.create(1, 9999, "owner")
except Exception as e:
    print(f"Error: {e}")  # "FOREIGN KEY constraint failed"


# ============================================================================
# 11. TESTING / DEVELOPMENT
# ============================================================================

from core import drop_all_tables

# Reset database (development only!)
drop_all_tables()
init_database()
# All data is now gone, tables are fresh

