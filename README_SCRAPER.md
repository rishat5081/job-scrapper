# 🎯 Automated Job Tracker with Web Scraping

**A complete job search automation system that scrapes jobs from multiple sources and displays them in a live dashboard with macOS notifications.**

---

## 🚀 Quick Start (Copy & Paste)

### 1. Install Dependencies

Open Terminal in this folder and run:

```bash
cd /Users/user/Desktop/Work/jobs
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Scrape Your First Jobs

```bash
source venv/bin/activate
python job_scraper.py scrape
```

You'll see:
- Jobs being scraped from Remotive, We Work Remotely, and Remote OK
- A macOS notification when complete
- Total number of jobs found

### 3. Start the Dashboard

```bash
./start_server.sh
```

Then open: **http://localhost:5000**

---

## 🌟 Features

### ✨ Automatic Job Scraping
- Scrapes from **Remotive**, **We Work Remotely**, and **Remote OK**
- Filters for **senior software engineering** positions
- Focuses on **Dubai, Netherlands, Germany**, and **Remote** opportunities
- Removes duplicates automatically

### 📊 Live Dashboard
- Beautiful web interface at `http://localhost:5000`
- Real-time job listings with all details
- Search by company, title, or keywords
- Filter by location (Dubai, Netherlands, Germany, Remote)
- One-click to track jobs

### 🔔 macOS Notifications
- Get notified when new jobs are found
- Alerts when scraping completes
- Notifications when you track a job

### 📝 Application Tracking
- Track jobs you're interested in
- Update status: New → Applied → Interview → Offer/Rejected
- Add notes for each application
- See all tracked jobs in sidebar

### 🔄 Automated Scraping (Optional)
- Set up automatic scraping every 3 hours
- Runs in background
- Keeps your job list fresh

---

## 📁 System Overview

### What Gets Scraped:
- **Job Title** - Position name
- **Company** - Company name
- **Location** - Dubai, Netherlands, Germany, or Remote
- **Salary** - When available
- **Description** - Job description (first 500 chars)
- **URL** - Direct link to application
- **Source** - Which job board it came from
- **Date Posted** - When the job was posted

### How It Works:

```
1. Job Scraper (job_scraper.py)
   ↓
   Fetches jobs from multiple APIs/websites
   ↓
2. Saves to scraped_jobs.json
   ↓
3. Flask API (api_server.py)
   ↓
   Serves data to dashboard
   ↓
4. Live Dashboard (live_dashboard.html)
   ↓
   Display jobs + Track applications
```

---

## 🎮 Usage

### Manual Scraping

Activate the virtual environment first:
```bash
source venv/bin/activate
```

Then scrape:
```bash
python job_scraper.py scrape
```

List scraped jobs:
```bash
python job_scraper.py list
```

### Start Dashboard

```bash
./start_server.sh
```

Or manually:
```bash
source venv/bin/activate
python api_server.py
```

### Setup Automated Scraping

Scrape automatically every 3 hours:

```bash
./setup_auto_scraper.sh
```

Disable automated scraping:
```bash
launchctl unload ~/Library/LaunchAgents/com.jobtracker.scraper.plist
```

Re-enable:
```bash
launchctl load ~/Library/LaunchAgents/com.jobtracker.scraper.plist
```

---

## 📊 Dashboard Features

### Available Jobs Section (Left)
- All scraped jobs displayed as cards
- Click any card to open the job listing
- **"Track This"** button - Add to your tracker
- **"View Job"** button - Open in new tab
- Shows: Company, Title, Location, Salary, Source, Date
- Live search across all fields
- Filter by location

### Tracked Jobs Section (Right)
- Your tracked/applied jobs
- Status badges: New, Applied, Interview, Offer, Rejected
- Quick action buttons
- Click "View" to see original listing
- Update status with one click

### Top Bar
- **🔄 Scrape Jobs Now** - Manual scrape trigger
- **Last Scraped** - Shows when data was last updated
- **Search Box** - Find specific jobs
- **Statistics** - Total scraped, tracked, applied, interviews

---

## 🔧 Configuration

### Change Scraping Interval

Edit `setup_auto_scraper.sh`, find this line:
```xml
<key>StartInterval</key>
<integer>10800</integer>
```

Change `10800` to:
- `3600` = 1 hour
- `7200` = 2 hours
- `21600` = 6 hours

### Add More Job Sources

Edit `job_scraper.py` and add new scraping functions. Example:

```python
def scrape_your_source():
    jobs = []
    # Your scraping logic here
    return jobs
```

Then call it in `scrape_all_jobs()`:

```python
all_new_jobs.extend(scrape_your_source())
```

---

## 📂 File Structure

```
jobs/
├── live_dashboard.html      # Main dashboard (served by Flask)
├── api_server.py            # Flask backend API
├── job_scraper.py           # Web scraping logic
├── job_monitor.py           # CLI job tracker (legacy)
├── start_server.sh          # Quick start script
├── auto_scraper.sh          # Automated scraping script
├── setup_auto_scraper.sh    # Setup auto-scraping
├── setup_alerts.sh          # Setup reminder alerts
├── check_jobs.sh            # Manual reminder
├── requirements.txt         # Python dependencies
├── venv/                    # Virtual environment
├── scraped_jobs.json        # Scraped jobs database
├── job_tracker.json         # Tracked applications
├── last_scrape.json         # Last scrape info
└── README_SCRAPER.md        # This file
```

---

## 🛠️ Troubleshooting

### "Cannot connect to server" in dashboard

Make sure the server is running:
```bash
./start_server.sh
```

### No jobs after scraping

Check if scraping worked:
```bash
source venv/bin/activate
python job_scraper.py scrape
```

Check the output for errors.

### Dependencies not installed

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Virtual environment issues

Recreate it:
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Port 5000 already in use

Edit `api_server.py`, change the last line:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change to 5001
```

Then access: `http://localhost:5001`

---

## 💡 Tips for Success

1. **Scrape 2-3 times daily** - Morning, noon, and evening for best coverage
2. **Enable notifications** - Never miss new opportunities
3. **Use search** - Find jobs matching your specific tech stack
4. **Track everything interesting** - You can always remove later
5. **Update statuses** - Stay organized throughout your search
6. **Set up auto-scraping** - Run in background while you work
7. **Check the dashboard daily** - Make it part of your routine

---

## 🎯 Workflow Recommendation

### Daily Routine:

**Morning (9 AM)**
1. Open dashboard: `http://localhost:5000`
2. Click "Scrape Jobs Now"
3. Browse new jobs
4. Track interesting positions
5. Apply to 2-3 jobs

**Afternoon (2 PM)**
1. Scrape again
2. Check for new listings
3. Update application statuses

**Evening (6 PM)**
1. Final scrape of the day
2. Review tracked jobs
3. Prepare applications for tomorrow

---

## 📈 Expected Results

- **Initial Scrape**: 30-60 jobs
- **Daily New Jobs**: 5-15 jobs
- **Response Rate**: Track at least 10-15 jobs per week
- **Interview Rate**: Apply to 20-30 jobs per week

---

## 🔐 Privacy & Data

- ✅ All data stored **locally** on your Mac
- ✅ No external database or cloud service
- ✅ Your applications tracked **privately**
- ✅ No data sent to third parties
- ✅ Simple JSON files you can inspect anytime

---

## 🚀 Advanced Usage

### Run scraper on a schedule (cron alternative)

Instead of launchd, use a cron job:

```bash
crontab -e
```

Add:
```
0 */3 * * * cd /Users/user/Desktop/Work/jobs && ./auto_scraper.sh
```

### Export tracked jobs

```bash
cat job_tracker.json | python -m json.tool > my_applications.json
```

### Backup your data

```bash
cp scraped_jobs.json scraped_jobs_backup.json
cp job_tracker.json job_tracker_backup.json
```

---

## 🤝 Contributing Ideas

Want to improve the scraper? Consider adding:

- LinkedIn job scraping (requires API key)
- Indeed scraping (more complex)
- Glassdoor integration
- Email alerts instead of macOS notifications
- Export to CSV/Excel
- Statistics dashboard
- Application timeline view

---

## 📞 Need Help?

Check the logs:
```bash
# Scraper logs
cat scraper.log

# Server logs
# (printed in terminal where you ran start_server.sh)
```

Test the scraper manually:
```bash
source venv/bin/activate
python job_scraper.py scrape
```

---

## ✅ Checklist

- [ ] Created virtual environment
- [ ] Installed dependencies
- [ ] Ran first scrape successfully
- [ ] Started dashboard server
- [ ] Opened dashboard in browser
- [ ] Enabled notifications
- [ ] Tracked first job
- [ ] Set up automated scraping (optional)
- [ ] Added to daily routine

---

**Good luck with your senior software engineering job search!** 🎉

*Built with Python, Flask, BeautifulSoup, and Claude Code*
