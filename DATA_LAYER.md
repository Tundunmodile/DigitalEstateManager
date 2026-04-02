# Data Layer Documentation
## Digital Estate Manager

---

## 📋 Overview

The data layer provides a complete SQLite-based persistence system for the Digital Estate Manager application. It uses a universal CRUD function pattern with Data Access Objects (DAOs) for type safety and clean separation of concerns.

**File**: `core/database.py` (470+ lines, fully documented)  
**Database**: SQLite at `./data/estate_manager.db`  
**Initialization**: Automatic on app startup via `init_database()`

---

## 🏗️ Architecture

### Core Components

```
┌─────────────────────────────────────────┐
│         Application Layer               │
│  (app.py, Event Loops, Chat Service)    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      DAO Layer (Abstraction)            │
│  UserDAO, AssetDAO, VendorDAO, etc      │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│    Universal CRUD Function              │
│  execute_sqlite_query()                 │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│    SQLite Database (7 Tables)           │
│  ./data/estate_manager.db               │
└─────────────────────────────────────────┘
```

### Database Schema

#### 1. **Users Table**
Stores user credentials for the estate/property manager.
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,              -- plain text for MVP (enhance later)
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. **Assets Table** (Properties)
Represents properties managed by the company.
```sql
CREATE TABLE assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_name TEXT NOT NULL,         -- "Suburban Home", "Downtown Condo"
    address TEXT NOT NULL UNIQUE,        -- Full address (enforces uniqueness)
    property_type TEXT NOT NULL,         -- house, condo, apartment, commercial
    square_footage INTEGER,              -- Optional
    year_built INTEGER,                  -- Optional
    description TEXT,                    -- Notes about the property
    status TEXT DEFAULT 'active',        -- active, inactive, archived
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### 3. **Customer-Assets Join Table**
Maps users to their managed properties (1-to-many relationship).
```sql
CREATE TABLE customer_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,            -- FK → users.id
    asset_id INTEGER NOT NULL,           -- FK → assets.id
    relationship_type TEXT NOT NULL,     -- owner, manager, tenant
    assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, asset_id)            -- Prevent duplicates
);
```

#### 4. **Vendors Table**
Service providers (cleaners, plumbers, electricians, landscapers).
```sql
CREATE TABLE vendors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_name TEXT NOT NULL,
    service_type TEXT NOT NULL,          -- cleaning, plumbing, electrical, etc
    contact_name TEXT,                   -- Person to contact
    phone TEXT,                          -- Contact number
    email TEXT,                          -- Contact email
    rating REAL DEFAULT 0.0,             -- 1-5 star rating
    notes TEXT,                          -- Additional info
    status TEXT DEFAULT 'active',        -- active, inactive
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### 5. **Schedules Table**
Historical and upcoming service schedules.
```sql
CREATE TABLE schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,           -- FK → assets.id (property)
    vendor_id INTEGER NOT NULL,          -- FK → vendors.id
    service_type TEXT NOT NULL,          -- Type of service
    scheduled_date DATE NOT NULL,        -- When service is scheduled
    scheduled_time TIME,                 -- What time
    completion_date TIMESTAMP,           -- When service was completed (NULL if not done)
    status TEXT DEFAULT 'scheduled',     -- scheduled, in_progress, completed, cancelled
    notes TEXT,                          -- Service notes
    cost REAL,                           -- Service cost
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### 6. **Event Audit Table**
Audit trail of all critical operations (for debugging + compliance).
```sql
CREATE TABLE event_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,            -- Type of event from EventBus
    source TEXT,                         -- Which loop/component created event
    data TEXT,                           -- JSON string with event data
    correlation_id TEXT,                 -- For tracing across loops
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes (Performance Optimization)

```sql
CREATE INDEX idx_customer_assets_user_id ON customer_assets(user_id);
CREATE INDEX idx_customer_assets_asset_id ON customer_assets(asset_id);
CREATE INDEX idx_schedules_asset_id ON schedules(asset_id);
CREATE INDEX idx_schedules_vendor_id ON schedules(vendor_id);
CREATE INDEX idx_schedules_date ON schedules(scheduled_date);
CREATE INDEX idx_event_audit_type ON event_audit(event_type);
CREATE INDEX idx_event_audit_correlation ON event_audit(correlation_id);
```

---

## 🔧 Core Function: `execute_sqlite_query()`

The universal CRUD function for all database operations. Handles SELECT, INSERT, UPDATE, DELETE with automatic connection pooling and parameterized queries.

### Signature
```python
def execute_sqlite_query(
    query: str,
    params: Tuple = (),
    operation_type: str = "SELECT",
    fetch: str = "all"
) -> Any
```

### Parameters
- **query** (str): SQL query with `?` placeholders
- **params** (tuple): Values to bind (prevents SQL injection)
- **operation_type** (str): "SELECT", "INSERT", "UPDATE", "DELETE" (for logging)
- **fetch** (str): Return mode:
  - `"all"` → List of dicts (all rows)
  - `"one"` → Single dict or None
  - `"count"` → Number of affected rows
  - `"lastid"` → Last inserted row ID

### Examples

#### SELECT - Get all users
```python
from core import execute_sqlite_query

users = execute_sqlite_query(
    "SELECT * FROM users WHERE status = ?",
    ("active",),
    operation_type="SELECT",
    fetch="all"
)
# Returns: [{"id": 1, "username": "manager1", ...}, ...]
```

#### INSERT - Create new vendor
```python
vendor_id = execute_sqlite_query(
    "INSERT INTO vendors (vendor_name, service_type, phone) VALUES (?, ?, ?)",
    ("Clean Pro", "cleaning", "555-1234"),
    operation_type="INSERT",
    fetch="lastid"
)
# Returns: 42  (the new vendor's ID)
```

#### UPDATE - Change status
```python
rows_updated = execute_sqlite_query(
    "UPDATE schedules SET status = ? WHERE id = ?",
    ("completed", 1),
    operation_type="UPDATE",
    fetch="count"
)
# Returns: 1  (one row updated)
```

#### DELETE - Remove vendor
```python
rows_deleted = execute_sqlite_query(
    "DELETE FROM vendors WHERE id = ?",
    (1,),
    operation_type="DELETE",
    fetch="count"
)
# Returns: 1  (one row deleted)
```

---

## 📦 Data Access Objects (DAOs)

DAOs provide a clean, typed interface above raw SQL. Use these instead of calling `execute_sqlite_query()` directly.

### UserDAO

```python
from core import UserDAO

# Create user
user_id = UserDAO.create(
    username="manager1",
    password="demo_password",
    email="manager@example.com"
)

# Get user
user = UserDAO.get_by_id(1)
# Returns: {"id": 1, "username": "manager1", "email": "...", ...}

# Get by username (for login)
user = UserDAO.get_by_username("manager1")

# Get all users
users = UserDAO.get_all()

# Update user
UserDAO.update(1, email="newemail@example.com", password="newpass")

# Delete user
UserDAO.delete(1)
```

### AssetDAO

```python
from core import AssetDAO

# Create asset (property)
asset_id = AssetDAO.create(
    property_name="Suburban Home",
    address="123 Oak Street, Springfield, IL",
    property_type="house",
    square_footage=3500,
    year_built=1995,
    description="3BR/2BA with large yard"
)

# Get by ID
asset = AssetDAO.get_by_id(1)

# Get all assets
assets = AssetDAO.get_all()

# Get all assets for a user
user_assets = AssetDAO.get_by_user(user_id=1)
# Returns: [{"id": 1, "property_name": "Suburban Home", ...}, ...]

# Update asset
AssetDAO.update(1, status="archived")

# Delete asset
AssetDAO.delete(1)
```

### CustomerAssetDAO

```python
from core import CustomerAssetDAO

# Assign asset to user
relationship_id = CustomerAssetDAO.create(
    user_id=1,
    asset_id=1,
    relationship_type="owner"  # or "manager", "tenant"
)

# Get all assets for a user
assignments = CustomerAssetDAO.get_all_for_user(user_id=1)

# Get all users managing an asset
managers = CustomerAssetDAO.get_all_for_asset(asset_id=1)

# Remove assignment
CustomerAssetDAO.delete(user_id=1, asset_id=1)
```

### VendorDAO

```python
from core import VendorDAO

# Create vendor
vendor_id = VendorDAO.create(
    vendor_name="Clean Pro Services",
    service_type="cleaning",
    contact_name="Sarah Johnson",
    phone="(555) 123-4567",
    email="sarah@cleanpro.com",
    notes="Excellent attention to detail"
)

# Get by ID
vendor = VendorDAO.get_by_id(1)

# Get all vendors
vendors = VendorDAO.get_all()

# Get vendors by service type
cleaners = VendorDAO.get_by_service_type("cleaning")
# Returns vendors with highest ratings first

# Update vendor
VendorDAO.update(1, rating=4.8)

# Delete vendor (soft delete via status)
VendorDAO.delete(1)  # Sets status to 'inactive'
```

### ScheduleDAO

```python
from core import ScheduleDAO

# Create schedule
schedule_id = ScheduleDAO.create(
    asset_id=1,
    vendor_id=1,
    service_type="cleaning",
    scheduled_date="2026-04-05",
    scheduled_time="10:00",
    notes="Biweekly deep clean",
    cost=150.00
)

# Get by ID
schedule = ScheduleDAO.get_by_id(1)

# Get all schedules for an asset
schedules = ScheduleDAO.get_all_for_asset(asset_id=1)

# Get upcoming schedules (next 30 days)
upcoming = ScheduleDAO.get_upcoming(asset_id=1, days_ahead=30)

# Update schedule
ScheduleDAO.update(1, status="in_progress")

# Mark as completed
ScheduleDAO.mark_completed(1, completion_date="2026-04-05T14:30:00")
```

### EventAuditDAO

```python
from core import EventAuditDAO
import json

# Log an event
log_id = EventAuditDAO.log_event(
    event_type="OPERATION_COMPLETED",
    source="SchedulerAgent",
    data=json.dumps({"task": "schedule_cleaning", "vendor_id": 1}),
    correlation_id="corr-123-456"
)

# Get events by correlation ID (trace across loops)
events = EventAuditDAO.get_by_correlation_id("corr-123-456")

# Get recent events of a type
recent = EventAuditDAO.get_by_type("OPERATION_COMPLETED", limit=50)
```

---

## 🚀 Initialization & Maintenance

### Initialize Database

```python
from core import init_database

# Safe to call multiple times (uses "IF NOT EXISTS")
init_database()
# Creates all tables + indexes if they don't exist
```

### Get Database Statistics

```python
from core import get_database_stats

stats = get_database_stats()
# Returns: {"users": 5, "assets": 12, "vendors": 8, "schedules": 24, ...}
```

### Drop All Tables (Development Only!)

```python
from core import drop_all_tables

drop_all_tables()  # ⚠️ Deletes ALL data. Use with caution!
```

---

## 🔌 Integration with Event-Driven Architecture

### 1. OpsLayer Publishing Schedule Results

```python
from core import ScheduleDAO, execute_sqlite_query
from core import get_event_bus, Event, EventType

# When an operation completes, save to database
schedule_id = ScheduleDAO.create(
    asset_id=operation_data["asset_id"],
    vendor_id=operation_data["vendor_id"],
    service_type=operation_data["service_type"],
    scheduled_date=operation_data["scheduled_date"]
)

# Also log to event audit
EventAuditDAO.log_event(
    event_type="OPERATION_COMPLETED",
    source="OpsLayer",
    data=json.dumps(operation_data),
    correlation_id=event.correlation_id
)

# Publish completion event
event_bus.publish(Event(
    event_type=EventType.OPERATION_COMPLETED,
    source="OpsLayer",
    data={"schedule_id": schedule_id, ...},
    correlation_id=event.correlation_id
))
```

### 2. ProactiveEngineLoop Reading Home State

```python
from core import AssetDAO, ScheduleDAO

# Get all assets for user to analyze
assets = AssetDAO.get_by_user(user_id=1)

for asset in assets:
    # Get upcoming services for this asset
    upcoming = ScheduleDAO.get_upcoming(asset["id"], days_ahead=7)
    
    # Generate proactive suggestions based on state
    if len(upcoming) == 0:
        # Suggest scheduling maintenance
```

### 3. EventBus Audit Trail

```python
from core import EventAuditDAO
import json

# All critical events logged to database
EventAuditDAO.log_event(
    event_type=event.event_type.name,
    source=event.source,
    data=json.dumps(event.data),
    correlation_id=event.correlation_id
)
```

---

## 🧪 Testing

### Run Demo Tests
```bash
python3 app.py
```

Output shows:
- ✓ Database initialization
- ✓ User creation
- ✓ Asset creation (2 properties)
- ✓ Vendor creation (2 vendors)
- ✓ Schedule creation (2 services)
- ✓ Data retrieval and filtering

### Query Database Directly
```bash
sqlite3 data/estate_manager.db "SELECT * FROM users;"
sqlite3 data/estate_manager.db "SELECT * FROM schedules WHERE status='completed';"
```

---

## 🛡️ Security Considerations

✅ **Parameterized Queries**: All user input bound with `?` placeholders (prevents SQL injection)  
✅ **Foreign Key Enforcement**: Enabled to prevent orphaned records  
✅ **Unique Constraints**: On username, email, address to prevent duplicates  
✅ **Timestamps**: created_at/updated_at for audit trails  

⚠️ **TODO (Phase 2)**:
- Password hashing (use `bcrypt` or `argon2`)
- User authentication/authorization
- Permission checks (can user access this asset?)
- Encryption of sensitive vendor data

---

## 📈 Performance Notes

- **Indexes**: 7 carefully chosen indexes for fast queries
- **Pagination**: For large datasets, add LIMIT/OFFSET to queries
- **Batch Operations**: For bulk inserts, wrap in transaction manually
- **Query Optimization**: Use `.get_upcoming()` instead of loading all schedules

---

## 🐛 Troubleshooting

### Database File Not Found
- Check file path: `./data/estate_manager.db`
- Ensure `data/` directory exists and is writable
- Run `init_database()` to create schema

### Foreign Key Constraint Violation
- Ensure referenced user/asset/vendor exists before creating relationship
- Check `customer_assets` join table for orphaned assignments

### Slow Queries
- Check that indexes exist: `sqlite3 data/estate_manager.db ".indices"`
- Add WHERE clause filters to reduce result set
- Use `get_upcoming()` instead of `get_all_for_asset()`

### Duplicate Entry Error
- Username, email, address are UNIQUE
- Check `CustomerAssetDAO` UNIQUE constraint on (user_id, asset_id)

---

## 📚 Related Documentation

- [Event-Driven Architecture](event-driven-architecture.md)
- [Task Extraction System](task-extraction-system.md)
- [Database Initialization](core/database.py)

