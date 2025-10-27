# System Architecture

This document describes the architecture and data flow of the Road Painting Bot system.

## System Overview

```
┌─────────────┐
│   Telegram  │
│    Users    │
└──────┬──────┘
       │
       ├── Send messages
       ├── Upload photos
       └── Share location
       │
       ▼
┌──────────────────────────────────────────────────┐
│                                                  │
│              Telegram Bot API                    │
│                                                  │
└───────────────────┬──────────────────────────────┘
                    │
                    │ HTTP/HTTPS
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│                                                 │
│           Road Painting Bot Application         │
│                  (bot.py)                       │
│                                                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐      ┌──────────────┐       │
│  │   Config     │      │   Database   │       │
│  │  (config.py) │      │(database.py) │       │
│  └──────────────┘      └──────────────┘       │
│                                                 │
│  ┌─────────────────────────────────────────┐  │
│  │          Handlers                       │  │
│  │  ┌─────────────┐  ┌─────────────┐      │  │
│  │  │    User     │  │  Inspector  │      │  │
│  │  │  Handlers   │  │  Handlers   │      │  │
│  │  └─────────────┘  └─────────────┘      │  │
│  └─────────────────────────────────────────┘  │
│                                                 │
└─────────────────┬───────────────────────────────┘
                  │
                  │ SQLite
                  │
                  ▼
          ┌──────────────┐
          │   Database   │
          │road_painting │
          │     .db      │
          └──────────────┘
```

## Component Architecture

```
┌──────────────────────────────────────────────────────────┐
│                       bot.py                             │
│  ┌────────────────────────────────────────────────────┐  │
│  │  • Application initialization                      │  │
│  │  • Handler registration                            │  │
│  │  • Error handling                                  │  │
│  │  • Logging setup                                   │  │
│  │  • Graceful shutdown                               │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                          │
           ┌──────────────┼──────────────┐
           │              │              │
           ▼              ▼              ▼
    ┌───────────┐  ┌───────────┐  ┌───────────┐
    │  config.py│  │database.py│  │ handlers/ │
    └───────────┘  └───────────┘  └───────────┘
         │              │              │
         │              │              └─────┬──────┐
         │              │                    │      │
         ▼              ▼                    ▼      ▼
    ┌─────────┐   ┌──────────┐      ┌──────────┐ ┌──────────┐
    │  .env   │   │  SQLite  │      │   user_  │ │inspector_│
    │  file   │   │ Database │      │ handlers │ │ handlers │
    └─────────┘   └──────────┘      └──────────┘ └──────────┘
```

## Data Flow

### User Submission Flow

```
┌──────┐
│ User │
└───┬──┘
    │
    │ 1. /report
    ▼
┌─────────────┐
│  Bot Sends  │
│  "Send      │
│   Photo"    │
└──────┬──────┘
       │
       │ 2. Photo
       ▼
┌─────────────┐
│ Store photo │
│   file_id   │
│ in context  │
└──────┬──────┘
       │
       │ 3. Request Location
       ▼
┌─────────────┐
│  Bot Sends  │
│ Location    │
│  Button     │
└──────┬──────┘
       │
       │ 4. Location
       ▼
┌─────────────┐
│ Store lat/  │
│ lon in      │
│ context     │
└──────┬──────┘
       │
       │ 5. Confirmation Request
       ▼
┌─────────────┐
│ Show        │
│ Summary     │
└──────┬──────┘
       │
       │ 6. "yes"
       ▼
┌─────────────┐
│  Save to    │
│  Database   │
└──────┬──────┘
       │
       │ 7. Confirmation + ID
       ▼
┌──────┐
│ User │
└──────┘
```

### Inspector Review Flow

```
┌───────────┐
│ Inspector │
└─────┬─────┘
      │
      │ 1. /pending
      ▼
┌──────────────┐
│ Query DB for │
│  pending     │
│ submissions  │
└──────┬───────┘
       │
       │ 2. For each submission
       ▼
┌──────────────────────┐
│  Send:               │
│  • Photo             │
│  • User info         │
│  • Location          │
│  • Inline buttons    │
│    [Approve][Reject] │
└──────────┬───────────┘
           │
           │ 3. Click button
           ▼
┌──────────────────────┐
│  Callback Handler:   │
│  • Update DB status  │
│  • Record inspector  │
│  • Timestamp         │
└──────────┬───────────┘
           │
           ├─────────────┬──────────────┐
           │             │              │
           │ 4a. Notify  │ 4b. Update   │
           │    User     │   Message    │
           ▼             ▼              │
     ┌─────────┐   ┌──────────┐        │
     │  User   │   │Inspector │        │
     │Gets     │   │  Sees    │        │
     │Notif.   │   │ Result   │        │
     └─────────┘   └──────────┘        │
                                        ▼
                                   ┌─────────┐
                                   │  Save   │
                                   │   to    │
                                   │   DB    │
                                   └─────────┘
```

## Database Schema

```
┌────────────────────────────────────────┐
│           submissions                  │
├────────────────────────────────────────┤
│ id                 INTEGER PK AUTO     │
│ user_id            INTEGER NOT NULL    │
│ username           TEXT                │
│ first_name         TEXT                │
│ last_name          TEXT                │
│ photo_id           TEXT NOT NULL       │
│ latitude           REAL NOT NULL       │
│ longitude          REAL NOT NULL       │
│ timestamp          DATETIME NOT NULL   │
│ status             TEXT NOT NULL       │
│ inspector_id       INTEGER             │
│ inspector_username TEXT                │
│ decision_timestamp DATETIME            │
│ rejection_reason   TEXT                │
│ notes              TEXT                │
└────────────────────────────────────────┘
         │
         │ Indexes:
         ├─── idx_user_id
         ├─── idx_status
         └─── idx_timestamp
```

## State Management

### Conversation States (User Report Flow)

```
START
  │
  ▼
PHOTO ──────> Receive photo
  │
  │ photo received
  │
  ▼
LOCATION ───> Receive location
  │
  │ location received
  │
  ▼
CONFIRM ────> Confirm submission
  │
  │ "yes"
  │
  ▼
END (Save to DB)

At any point:
/cancel ────> END (Clear context)
```

### Context Data Structure

```python
context.user_data = {
    'photo_id': 'AgACAgIAAxkB...',  # Telegram file ID
    'photo_size': 123456,             # File size in bytes
    'latitude': 40.7128,              # GPS latitude
    'longitude': -74.0060             # GPS longitude
}
```

## Handler Registration Order

```
1. User Commands
   ├── /start
   ├── /help
   └── /status

2. Conversation Handler (/report)
   ├── Entry: /report
   ├── States: PHOTO → LOCATION → CONFIRM
   └── Fallback: /cancel

3. Inspector Commands
   ├── /inspector
   ├── /pending
   ├── /history
   ├── /stats
   └── /export

4. Callback Handlers
   └── approve_*, reject_*, map_*

5. Unknown Command Handler
   └── Catches all unregistered commands

6. Error Handler
   └── Global error handler
```

## Message Flow

### Incoming Message Processing

```
Telegram API
     │
     ▼
Application
     │
     ├──> Filters check
     │    (command, text, photo, location)
     │
     ├──> Handler matched?
     │    │
     │    ├─ Yes ──> Execute handler
     │    │          │
     │    │          ├──> Process
     │    │          │
     │    │          ├──> Database ops
     │    │          │
     │    │          └──> Reply to user
     │    │
     │    └─ No ───> Unknown command handler
     │
     └──> Error? ──> Error handler
```

## Web Dashboard Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP
       ▼
┌──────────────────┐
│  Flask Server    │
│ (web_dashboard)  │
├──────────────────┤
│                  │
│  Routes:         │
│  ├─ /           │───> HTML Dashboard
│  ├─ /api/sub... │───> JSON API
│  └─ /api/stats  │───> JSON API
│                  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Database Module │
│  (database.py)   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  SQLite DB       │
└──────────────────┘

Frontend:
┌──────────────────┐
│  Leaflet.js      │───> Interactive Map
│  OpenStreetMap   │───> Tile Server
└──────────────────┘
```

## Security Flow

```
┌──────────┐
│  Request │
└─────┬────┘
      │
      ▼
┌──────────────────┐
│ Inspector Check  │
│                  │
│ Config.is_       │
│ inspector(id)    │
└────┬─────────────┘
     │
     ├─── Authorized ──> Process request
     │
     └─── Not Auth. ──> "Access Denied"
```

## Logging Flow

```
┌──────────────┐
│   Event      │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│  Logger              │
│  (logging module)    │
└───────┬──────────────┘
        │
        ├──────────┬──────────┐
        │          │          │
        ▼          ▼          ▼
    ┌─────┐  ┌─────────┐  ┌──────┐
    │DEBUG│  │  INFO   │  │ERROR │
    └──┬──┘  └────┬────┘  └───┬──┘
       │          │           │
       ▼          ▼           ▼
┌──────────────────────────────┐
│     Console Handler          │
│   (stdout with colors)       │
└──────────────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│      File Handler            │
│      (bot.log)               │
└──────────────────────────────┘
```

## Deployment Architecture

### Development

```
┌──────────────┐
│  Developer   │
│   Machine    │
├──────────────┤
│ python bot.py│
│              │
│ ├─ bot.py   │
│ ├─ .env     │
│ └─ *.db     │
└──────────────┘
```

### Docker Deployment

```
┌──────────────────────────────┐
│      Docker Host             │
├──────────────────────────────┤
│                              │
│  ┌────────────────────────┐  │
│  │  Bot Container         │  │
│  │  ┌──────────────────┐  │  │
│  │  │  Application     │  │  │
│  │  └──────────────────┘  │  │
│  │  Volume: /app/data    │  │
│  └────────────────────────┘  │
│                              │
│  ┌────────────────────────┐  │
│  │  Dashboard Container   │  │
│  │  ┌──────────────────┐  │  │
│  │  │  Flask App       │  │  │
│  │  └──────────────────┘  │  │
│  │  Port: 5000          │  │
│  └────────────────────────┘  │
│                              │
│  ┌────────────────────────┐  │
│  │   Shared Volume        │  │
│  │   (Database & Logs)    │  │
│  └────────────────────────┘  │
└──────────────────────────────┘
```

## Error Handling Strategy

```
┌─────────────┐
│  Operation  │
└──────┬──────┘
       │
       ▼
    try:
    ┌────────────┐
    │  Execute   │
    └─────┬──────┘
          │
    ┌─────▼──────┐
    │ Success?   │
    └─────┬──────┘
          │
    ┌─────┴─────┐
    │           │
   YES         NO
    │           │
    │      except:
    │      ┌──────────┐
    │      │ Log error│
    │      └────┬─────┘
    │           │
    │           ▼
    │      ┌──────────────┐
    │      │ User-friendly│
    │      │   message    │
    │      └──────────────┘
    │
    ▼
┌─────────┐
│Continue │
└─────────┘
```

## Configuration Loading

```
Startup
  │
  ▼
┌────────────────┐
│ Load .env file │
│ (dotenv)       │
└────────┬───────┘
         │
         ▼
┌────────────────┐
│ Config class   │
│ reads env vars │
└────────┬───────┘
         │
         ▼
┌────────────────┐
│ Validate       │
│ required vars  │
└────────┬───────┘
         │
    ┌────┴────┐
    │         │
  Valid?    Invalid
    │         │
    │         ▼
    │    ┌────────┐
    │    │ Raise  │
    │    │ Error  │
    │    └────────┘
    │
    ▼
┌────────────┐
│ Continue   │
│ startup    │
└────────────┘
```

## Performance Considerations

### Database Queries

```
Indexed Fields:
├── user_id     ───> Fast user lookups
├── status      ───> Fast status filtering
└── timestamp   ───> Fast chronological queries

Query Optimization:
├── Connection pooling via context managers
├── Limit clauses on all queries
└── Batch operations where possible
```

### Bot Performance

```
Rate Limiting:
└── Configurable per-user limits

Async Operations:
├── All handlers are async
├── Non-blocking I/O
└── Concurrent request handling

Resource Management:
├── Graceful shutdown
├── Connection cleanup
└── Memory-efficient context storage
```

## Scalability Paths

### Horizontal Scaling

```
┌──────────────┐
│ Load Balancer│
└──────┬───────┘
       │
   ┌───┴───┬───────┬───────┐
   │       │       │       │
   ▼       ▼       ▼       ▼
┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
│Bot 1│ │Bot 2│ │Bot 3│ │Bot N│
└──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘
   │       │       │       │
   └───────┴───┬───┴───────┘
               │
               ▼
        ┌──────────────┐
        │   Shared DB  │
        │  (PostgreSQL)│
        └──────────────┘
```

### Current Limitations

- Single bot instance (polling mode)
- SQLite (single-writer)
- In-memory context storage

### Future Improvements

- Webhook mode for multiple instances
- PostgreSQL for concurrent writes
- Redis for distributed context
- Message queue for async processing

---

This architecture is designed to be:
- **Simple**: Easy to understand and modify
- **Modular**: Components are independent
- **Scalable**: Can grow with demand
- **Maintainable**: Clear separation of concerns
