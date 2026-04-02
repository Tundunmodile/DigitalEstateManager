# Digital Estate Manager - 4-Layer Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        UI LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ FastAPI REST │  │ WebSocket    │  │ Chat Session │          │
│  │ Endpoints    │  │ Handler      │  │ Manager      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  (api/, websocket/, session/, request_models/)                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT LAYER                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ LLM Orchestration                                        │  │
│  │  ├─ llm_sql_generator.py (NL → SQL via LLM)            │  │
│  │  ├─ query_validator.py (security/compliance)           │  │
│  │  ├─ orchestrator.py (main coordinator)                 │  │
│  │  └─ prompt_templates/ (few-shot examples)              │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Event-Driven Architecture                              │  │
│  │  ├─ event_bus.py (pub/sub)                             │  │
│  │  ├─ loops.py (5 independent loops)                     │  │
│  │  └─ event_types.py (enum definitions)                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Agent Implementations                                   │  │
│  │  ├─ agents/scheduler_agent.py                          │  │
│  │  ├─ agents/vendor_agent.py                             │  │
│  │  ├─ agents/finance_agent.py                            │  │
│  │  └─ agents/concierge_agent.py                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Agent Utilities & Tools                                 │  │
│  │  ├─ utils/task_extractor.py (intent classification)    │  │
│  │  ├─ utils/response_formatter.py (output generation)    │  │
│  │  ├─ utils/urgency_detector.py (priority escalation)    │  │
│  │  ├─ utils/suggestion_engine.py (proactive ideas)       │  │
│  │  ├─ utils/confirmation_generator.py (feedback msgs)    │  │
│  │  └─ tools/ (tool definitions for agent use)            │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ MCP Servers (Model Context Protocol)                   │  │
│  │  ├─ mcp_server.py (MCP protocol implementation)        │  │
│  │  ├─ mcp_handlers/ (resource/tool handlers)             │  │
│  │  └─ mcp_tools/ (tools exposed to Claude via MCP)       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     DATA LAYER                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Database Core                                            │  │
│  │  ├─ database.py (connection, schema, execute_query)     │  │
│  │  ├─ migrations/ (schema versioning)                     │  │
│  │  └─ backup/ (backup management)                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Data Access Objects (DAO)                               │  │
│  │  ├─ daos/user_dao.py                                    │  │
│  │  ├─ daos/asset_dao.py                                   │  │
│  │  ├─ daos/vendor_dao.py                                  │  │
│  │  ├─ daos/schedule_dao.py                                │  │
│  │  └─ daos/audit_dao.py                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Models & Serializers                                    │  │
│  │  ├─ models/user.py                                      │  │
│  │  ├─ models/asset.py                                     │  │
│  │  ├─ models/vendor.py                                    │  │
│  │  └─ models/schedule.py                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                     SQLite Database
                   (estate_manager.db)

┌─────────────────────────────────────────────────────────────────┐
│                     EVAL LAYER (Future)                         │
│  ├─ benchmarks/ (performance tests)                            │
│  ├─ metrics/ (KPI collection)                                  │
│  ├─ test_suites/ (agent evaluation)                            │
│  └─ reporting/ (performance dashboards)                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer-by-Layer Breakdown

### 1. DATA LAYER (`data_layer/`)
**Purpose**: Encapsulate all database operations & access patterns

**Responsibilities**:
- ✅ Database connection management
- ✅ Schema definition & migrations
- ✅ CRUD operations via `execute_sqlite_query()`
- ✅ DAO classes (data access patterns)
- ✅ Data models & validation
- ✅ Audit trail logging

**Key Files**:
```
data_layer/
├── __init__.py
├── database.py          # Connection, schema, execute_sqlite_query()
├── migrations/          # Schema versioning (future)
├── daos/
│   ├── __init__.py
│   ├── user_dao.py
│   ├── asset_dao.py
│   ├── vendor_dao.py
│   ├── schedule_dao.py
│   └── audit_dao.py
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── asset.py
│   ├── vendor.py
│   └── schedule.py
└── validators/
    ├── __init__.py
    └── query_validators.py
```

**No imports from**: agent_layer, ui_layer (data layer is foundational)

---

### 2. AGENT LAYER (`agent_layer/`)
**Purpose**: All LLM orchestration, agent logic, and tool execution

**Responsibilities**:
- ✅ Convert natural language → executable operations (LLM-based SQL generation)
- ✅ Orchestrate multi-agent workflows (task routing, coordination)
- ✅ Manage event-driven loops (5 independent loops)
- ✅ Implement specialized agents (scheduler, vendor, finance, concierge)
- ✅ Provide tools to agents (task extraction, urgency detection, suggestions)
- ✅ MCP server implementation (for external Claude access)
- ✅ Tool definitions (what agents can do)

**Key Files**:
```
agent_layer/
├── __init__.py
├── orchestration/
│   ├── __init__.py
│   ├── llm_sql_generator.py     # NL → SQL via Claude
│   ├── query_validator.py        # Security & compliance checks
│   ├── orchestrator.py           # Main coordinator
│   └── prompt_templates/         # Few-shot examples
├── event_bus/
│   ├── __init__.py
│   ├── event_bus.py
│   ├── event_types.py
│   ├── loops.py                  # 5 independent loops
│   └── base_loop.py
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── scheduler_agent.py
│   ├── vendor_agent.py
│   ├── finance_agent.py
│   └── concierge_agent.py
├── tools/
│   ├── __init__.py
│   ├── task_extractor.py         # Intent classification
│   ├── response_formatter.py      # Response generation
│   ├── urgency_detector.py        # Priority escalation
│   ├── suggestion_engine.py       # Proactive suggestions
│   └── confirmation_generator.py  # Feedback messages
├── mcp_server/
│   ├── __init__.py
│   ├── mcp_server.py             # MCP protocol handler
│   ├── handlers/
│   │   ├── __init__.py
│   │   └── resource_handlers.py
│   └── tools/
│       ├── __init__.py
│       ├── query_tool.py          # execute_sqlite_query_tool
│       └── retrieve_tool.py       # Data retrieval tools
└── capabilities/
    ├── __init__.py
    └── tool_definitions.py        # Tool registry
```

**Imports from**: data_layer (DAO access)

---

### 3. UI LAYER (`ui_layer/`)
**Purpose**: All user-facing interfaces (REST API, WebSocket, session management)

**Responsibilities**:
- ✅ REST API endpoints (chat, history, settings)
- ✅ WebSocket handlers (real-time chat)
- ✅ Session/user management
- ✅ Request/response validation
- ✅ Chat history persistence
- ✅ Authentication & authorization

**Key Files**:
```
ui_layer/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app definition
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py              # /api/chat endpoints
│   │   ├── history.py           # /api/history endpoints
│   │   ├── settings.py          # /api/settings endpoints
│   │   └── health.py            # /api/health endpoints
│   └── middleware/
│       ├── __init__.py
│       └── auth.py              # Authentication
├── websocket/
│   ├── __init__.py
│   ├── connection_manager.py    # WebSocket lifecycle
│   └── handlers.py              # Message handlers
├── models/
│   ├── __init__.py
│   ├── request_models.py        # Pydantic schemas
│   └── response_models.py
├── session/
│   ├── __init__.py
│   ├── session_manager.py
│   └── chat_history.py
└── frontend/
    ├── static/                  # JS/CSS assets
    └── templates/               # HTML templates
```

**Imports from**: agent_layer (for orchestration), data_layer (for history)

---

### 4. EVAL LAYER (`eval_layer/`) - Placeholder for Future
**Purpose**: Agent evaluation, benchmarking, and metrics

**Structure** (future implementation):
```
eval_layer/
├── benchmarks/
│   ├── __init__.py
│   └── query_generation_benchmarks.py
├── metrics/
│   ├── __init__.py
│   ├── agent_metrics.py
│   └── query_metrics.py
├── test_suites/
│   ├── __init__.py
│   └── agent_eval_suite.py
└── reporting/
    ├── __init__.py
    └── dashboards.py
```

---

## Data Flow Examples

### Example 1: User Asks Question → Response
```
1. User types: "Show me all properties built after 2000"
   ↓ [UI Layer]
2. FastAPI receives POST /api/chat
   ↓ [UI Layer → Agent Layer]
3. Orchestrator.process_user_input() called
   ↓ [Agent Layer]
4. LLM SQL Generator: "SELECT * FROM assets WHERE year_built > 2000"
   ↓ [Agent Layer]
5. Query Validator: ✅ ALLOWED (SELECT only)
   ↓ [Agent Layer → Data Layer]
6. execute_sqlite_query() executes SQL
   ↓ [Data Layer → SQLite]
7. Results returned: 2 properties
   ↓ [Data Layer → Agent Layer]
8. Response Formatter: "Found 2 properties built after 2000: ..."
   ↓ [Agent Layer → UI Layer]
9. WebSocket sends to user: "Found 2 properties..."
   ↓ [UI Layer → User]
```

### Example 2: Schedule Maintenance (Multi-Agent)
```
1. User: "Book cleaning for property 1 next Thursday"
   ↓
2. AIParserLoop extracts task
   ↓
3. TaskEngineLoop routes to SchedulerAgent
   ↓
4. SchedulerAgent generates SQL: INSERT INTO schedules (...)
   ↓
5. Validator + execute_sqlite_query
   ↓
6. Event published: OPERATION_COMPLETED
   ↓
7. UpdateDistributorLoop generates confirmation
   ↓
8. UI sends: "✓ Cleaning booked for property 1, Thursday 10am"
```

---

## File Structure After Refactoring

```
DigitalEstateManager/
├── app.py                          # Main entry point
├── ARCHITECTURE.md                 # This file
├── requirements.txt
├── .env
├── .gitignore
│
├── data_layer/
│   ├── __init__.py
│   ├── database.py                 # (moved from core/)
│   ├── daos/
│   │   ├── __init__.py
│   │   ├── user_dao.py
│   │   ├── asset_dao.py
│   │   ├── vendor_dao.py
│   │   ├── schedule_dao.py
│   │   └── audit_dao.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── asset.py
│   │   └── schedule.py
│   └── validators/
│       ├── __init__.py
│       └── query_validators.py
│
├── agent_layer/
│   ├── __init__.py
│   ├── orchestration/
│   │   ├── __init__.py
│   │   ├── llm_sql_generator.py    # ✨ NEW
│   │   ├── query_validator.py      # ✨ NEW
│   │   ├── orchestrator.py         # ✨ NEW
│   │   └── prompt_templates/
│   ├── event_bus/
│   │   ├── __init__.py
│   │   ├── event_bus.py            # (from core/)
│   │   ├── event_types.py
│   │   ├── loops.py                # (from core/)
│   │   └── base_loop.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   ├── scheduler_agent.py      # (from agents/)
│   │   ├── vendor_agent.py
│   │   └── concierge_agent.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── task_extractor.py       # (from utils/)
│   │   ├── response_formatter.py  # (from utils/)
│   │   ├── urgency_detector.py
│   │   ├── suggestion_engine.py
│   │   └── confirmation_generator.py
│   ├── mcp_server/
│   │   ├── __init__.py
│   │   ├── mcp_server.py           # (from core/)
│   │   ├── handlers/
│   │   └── tools/
│   └── capabilities/
│       ├── __init__.py
│       └── tool_definitions.py
│
├── ui_layer/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                 # ✨ NEW FastAPI app
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py
│   │   │   ├── history.py
│   │   │   └── health.py
│   │   └── middleware/
│   │       ├── __init__.py
│   │       └── auth.py
│   ├── websocket/
│   │   ├── __init__.py
│   │   ├── connection_manager.py   # ✨ NEW
│   │   └── handlers.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── request_models.py       # ✨ NEW
│   │   └── response_models.py
│   └── session/
│       ├── __init__.py
│       ├── session_manager.py      # ✨ NEW
│       └── chat_history.py
│
├── eval_layer/
│   ├── __init__.py
│   ├── README.md                   # Placeholder for future
│   ├── benchmarks/
│   ├── metrics/
│   └── test_suites/
│
├── data/
│   └── estate_manager.db           # SQLite database
│
└── docs/
    ├── API.md                      # REST API documentation
    ├── AGENT_DEVELOPMENT.md        # Agent creation guide
    └── MCP_INTEGRATION.md          # MCP server guide
```

---

## Key Architectural Principles

| Principle | Implementation |
|-----------|-----------------|
| **Separation of Concerns** | Each layer has single responsibility |
| **No Circular Dependencies** | UI → Agent → Data (unidirectional) |
| **Data Access Isolation** | Only data_layer touches SQLite directly |
| **Agent Autonomy** | Agents communicate via event bus, not direct calls |
| **Tool Encapsulation** | Tools defined in agent_layer, not scattered |
| **API-First Design** | UI layer exposes REST + WebSocket interfaces |
| **Safety First** | Query validator blocks unsafe operations |
| **Auditability** | All operations logged to data_layer audit tables |

---

## Dependencies by Layer

**Data Layer Dependencies**:
- sqlite3 (stdlib)
- Optional: alembic (migrations)

**Agent Layer Dependencies**:
- anthropic (Claude LLM)
- aiosync (threading for loops)
- pydantic (validation)

**UI Layer Dependencies**:
- fastapi
- uvicorn
- websockets
- pydantic

**Eval Layer Dependencies** (future):
- pytest
- pytest-benchmark
- pandas (metrics)

---

## Migration Path

Phase 1: ✅ **Architecture Design** (you are here)
Phase 2: **Reorganize files** (data_layer, agent_layer, ui_layer directories)
Phase 3: **Update imports** (all modules point to new structure)
Phase 4: **Implement UI layer** (FastAPI + WebSocket)
Phase 5: **Implement orchestrator** (LLM SQL generation)
Phase 6: **Testing & validation**

