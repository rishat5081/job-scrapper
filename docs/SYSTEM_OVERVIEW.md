# 🎯 Job Tracker System - Complete Overview

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     JOB TRACKER SYSTEM                      │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  Job Scraper     │──────▶  Flask API       │──────▶  Live Dashboard  │
│  (job_scraper.py)│      │  (api_server.py) │      │  (Browser)       │
└──────────────────┘      └──────────────────┘      └──────────────────┘
        │                          │                          │
        │                          │                          │
        ▼                          ▼                          ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  scraped_jobs    │      │  job_tracker     │      │  Your Browser    │
│  .json           │      │  .json           │      │  localhost:5000  │
└──────────────────┘      └──────────────────┘      └──────────────────┘

        ▲
        │
┌──────────────────┐
│  Job Sources:    │
│  • Remotive      │
│  • We Work       │
│    Remotely      │
│  • Remote OK     │
└──────────────────┘
```

---

## 🔄 How It Works

### 1️⃣ **Job Scraping**

```
Job Scraper (job_scraper.py)
     │
     ├─▶ Fetches from Remotive API
     ├─▶ Scrapes We Work Remotely
     └─▶ Scrapes Remote OK
     │
     ├─ Filters: Senior roles only
     ├─ Filters: Software engineering
     ├─ Filters: Dubai/Netherlands/Germany/Remote
     └─ Removes duplicates
     │
     ▼
Saves to scraped_jobs.json
     │
     ▼
Sends macOS notification
```

### 2️⃣ **Dashboard Display**

```
Flask API Server (api_server.py)
     │
     ├─ Serves scraped_jobs.json
     ├─ Serves job_tracker.json
     ├─ Handles tracking operations
     └─ Provides REST API
     │
     ▼
Live Dashboard (http://localhost:5000)
     │
     ├─ Displays all jobs
     ├─ Search & filter
     ├─ Track jobs
     └─ Update statuses
```

### 3️⃣ **Job Tracking**

```
User clicks "Track This"
     │
     ▼
API adds to job_tracker.json
     │
     ▼
Dashboard updates
     │
     ▼
macOS notification sent
```

---

## 📊 Data Flow

```
┌─────────────┐
│ Job Boards  │
│ (Remotive,  │
│  WWR, ROK)  │
└──────┬──────┘
       │
       │ HTTP Requests
       ▼
┌─────────────┐
│   Scraper   │
│  Filters &  │
│  Processes  │
└──────┬──────┘
       │
       │ Write JSON
       ▼
┌─────────────┐
│  scraped_   │
│  jobs.json  │
└──────┬──────┘
       │
       │ Read via API
       ▼
┌─────────────┐
│  Flask API  │
│   Server    │
└──────┬──────┘
       │
       │ Serve HTTP
       ▼
┌─────────────┐      ┌─────────────┐
│  Dashboard  │◀────▶│    User     │
│  (Browser)  │      │  Tracking   │
└─────────────┘      └──────┬──────┘
                            │
                            │ Save
                            ▼
                     ┌─────────────┐
                     │ job_tracker │
                     │   .json     │
                     └─────────────┘
```

---

## 🎨 User Interface

### Dashboard Layout

```
┌────────────────────────────────────────────────────────────┐
│  🎯 Live Job Tracker - Senior Software Engineering        │
│  Dubai • Netherlands • Germany • Remote                    │
│  ┌────────────────────────────────────────────────────┐   │
│  │ [🔄 Scrape Now] Last: 2h ago  [Search jobs...]    │   │
│  └────────────────────────────────────────────────────┘   │
│  ┌──────┬──────┬──────┬──────┐                            │
│  │ 📊 60│ 📝 12│ 📤 8 │ 💼 2 │  Statistics               │
│  │ Jobs │Track │Apply │Inter │                            │
│  └──────┴──────┴──────┴──────┘                            │
└────────────────────────────────────────────────────────────┘

┌─────────────────────────┐  ┌──────────────────────────┐
│   📋 Available Jobs     │  │  ✅ Tracked Jobs         │
│                         │  │                          │
│ [All][Dubai][NL][DE]    │  │  Company X               │
│                         │  │  Senior Engineer         │
│ ┌─────────────────────┐ │  │  Status: Applied         │
│ │ Company Name        │ │  │  [View][Update]          │
│ │ Senior Engineer     │ │  │                          │
│ │ 📍 Netherlands      │ │  │  Company Y               │
│ │ 💰 €100k-€120k      │ │  │  Lead Engineer           │
│ │ [View][Track This]  │ │  │  Status: Interview       │
│ └─────────────────────┘ │  │  [View][Update]          │
│                         │  │                          │
│ ┌─────────────────────┐ │  └──────────────────────────┘
│ │ Another Company     │ │
│ │ ...                 │ │
│ └─────────────────────┘ │
└─────────────────────────┘
```

---

## 🔔 Notification Types

### 1. Scraping Complete
```
┌─────────────────────────────┐
│ 🎯 9 New Jobs Found!        │
│                             │
│ Found 9 new senior software │
│ engineering positions.      │
│ Check your dashboard!       │
└─────────────────────────────┘
```

### 2. Job Tracked
```
┌─────────────────────────────┐
│ Job Added to Tracker        │
│                             │
│ Added Company Name -        │
│ Senior Software Engineer    │
└─────────────────────────────┘
```

### 3. Reminder (if enabled)
```
┌─────────────────────────────┐
│ 🔔 Job Search Reminder      │
│                             │
│ Time to check for new       │
│ senior software engineering │
│ jobs!                       │
└─────────────────────────────┘
```

---

## 📁 File Structure

```
/Users/user/Desktop/Work/jobs/
│
├── 📘 Documentation
│   ├── START_HERE.md          ⭐ Read first!
│   ├── README_SCRAPER.md      📖 Complete guide
│   ├── SETUP_GUIDE.md         🔧 Setup details
│   ├── QUICK_REFERENCE.md     ⚡ Quick commands
│   └── SYSTEM_OVERVIEW.md     🏗️ This file
│
├── 🚀 Installation & Startup
│   ├── install.sh             📦 One-click install
│   └── start_server.sh        🎮 Start dashboard
│
├── 🤖 Core Application
│   ├── job_scraper.py         🔍 Web scraper
│   ├── api_server.py          🌐 Flask backend
│   ├── live_dashboard.html    📊 Main dashboard
│   └── requirements.txt       📋 Dependencies
│
├── 🔄 Automation
│   ├── auto_scraper.sh        ⏰ Auto scrape script
│   └── setup_auto_scraper.sh  ⚙️ Setup automation
│
├── 💾 Data Files
│   ├── scraped_jobs.json      📚 All scraped jobs
│   ├── job_tracker.json       ✅ Your applications
│   └── last_scrape.json       🕐 Last scrape time
│
├── 🐍 Virtual Environment
│   └── venv/                  📦 Python packages
│
└── 📊 Legacy/Manual Tools
    ├── dashboard.html         📋 Offline tracker
    ├── job_monitor.py         💻 CLI tool
    ├── check_jobs.sh          🔔 Manual reminder
    └── setup_alerts.sh        ⏰ Setup reminders
```

---

## ⚙️ Configuration

### Current Settings

| Setting | Value |
|---------|-------|
| **Auto-scrape interval** | 3 hours (10800 seconds) |
| **API Port** | 5000 |
| **Scrape timeout** | 10 seconds per request |
| **Job filters** | Senior + Software Engineering |
| **Locations** | Dubai, Netherlands, Germany, Remote |
| **Job sources** | Remotive, WWR, Remote OK |
| **Data storage** | Local JSON files |

### Customization Options

**Change scraping interval:**
Edit `setup_auto_scraper.sh`, line ~30:
```xml
<key>StartInterval</key>
<integer>10800</integer>  <!-- Change this -->
```

**Change API port:**
Edit `api_server.py`, last line:
```python
app.run(debug=True, host='0.0.0.0', port=5000)  # Change port
```

**Add job sources:**
Edit `job_scraper.py`, add new scraping function in `scrape_all_jobs()`

---

## 🎯 Job Filtering Logic

```python
# Filter criteria applied:

1. Job Title Contains:
   ✓ "senior"
   ✓ "lead"
   ✓ "sr."
   ✗ "junior"
   ✗ "intern"

2. Location Matches:
   ✓ Dubai / UAE
   ✓ Netherlands
   ✓ Germany
   ✓ Remote (Worldwide/Europe)
   ✗ Other specific countries

3. Category:
   ✓ Software Engineering
   ✓ Development
   ✓ Tech Lead
```

---

## 📊 Expected Performance

### Scraping Speed
- **First scrape:** 15-30 seconds
- **Subsequent scrapes:** 10-20 seconds
- **Jobs per scrape:** 30-60 initially, 5-15 new daily

### System Requirements
- **Python:** 3.7+
- **RAM:** ~50MB
- **Disk:** ~5MB for app + data
- **Network:** Stable internet connection

### Success Metrics
- **Daily new jobs:** 5-15
- **Weekly tracking goal:** 10-15 jobs
- **Weekly applications:** 5-10 jobs
- **Monthly interviews:** 4-12 scheduled

---

## 🔐 Privacy & Security

### Data Storage
- ✅ **All data stored locally** on your Mac
- ✅ **No cloud services** used
- ✅ **No external database** required
- ✅ **No analytics or tracking**

### What's Collected
- ✅ Job listings (public data)
- ✅ Your tracked applications (local only)
- ✅ Application notes (local only)

### What's NOT Collected
- ❌ Personal information
- ❌ Browsing history
- ❌ Usage analytics
- ❌ Any data sent to third parties

---

## 🚨 Error Handling

### Common Issues

**"Cannot connect to server"**
```
Solution: Start the server
$ ./start_server.sh
```

**"No jobs found"**
```
Solution: Run scraper manually
$ source venv/bin/activate
$ python job_scraper.py scrape
```

**"Dependencies not installed"**
```
Solution: Reinstall
$ ./install.sh
```

**"Port 5000 already in use"**
```
Solution: Kill existing process
$ lsof -ti:5000 | xargs kill -9
$ ./start_server.sh
```

---

## 📈 Roadmap & Future Features

### Possible Enhancements
- [ ] LinkedIn job scraping (requires API key)
- [ ] Indeed integration
- [ ] Email notifications
- [ ] Export to CSV/Excel
- [ ] Application timeline view
- [ ] Salary comparison charts
- [ ] Interview preparation notes
- [ ] Company research links
- [ ] Application deadline reminders

---

## 🎓 Learning Resources

### Technologies Used
- **Python** - Main programming language
- **Flask** - Web framework for API
- **BeautifulSoup** - Web scraping
- **Requests** - HTTP library
- **JSON** - Data storage
- **HTML/CSS/JavaScript** - Dashboard UI

### Useful Commands

```bash
# View logs
cat scraper.log

# Check scraped data
cat scraped_jobs.json | python -m json.tool

# Check tracked jobs
cat job_tracker.json | python -m json.tool

# View launchd jobs
launchctl list | grep jobtracker

# Python shell (for debugging)
source venv/bin/activate
python
>>> from job_scraper import *
>>> jobs = load_scraped_jobs()
>>> len(jobs)
```

---

## ✅ System Status Checklist

Check your system health:

- [ ] Virtual environment exists (`venv/` folder)
- [ ] Dependencies installed (run `./install.sh`)
- [ ] Scraper works (`python job_scraper.py scrape`)
- [ ] Server starts (`./start_server.sh`)
- [ ] Dashboard loads (`http://localhost:5000`)
- [ ] Jobs display in dashboard
- [ ] Can track jobs successfully
- [ ] Notifications work
- [ ] Auto-scraping enabled (optional)

---

**System Overview Complete!** 🎉

For quick reference, see: **QUICK_REFERENCE.md**
For getting started, see: **START_HERE.md**
For full documentation, see: **README_SCRAPER.md**
