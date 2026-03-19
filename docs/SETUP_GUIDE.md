# 🚀 Job Tracker with Web Scraping - Setup Guide

## 📋 What This System Does

This is an **automated job scraping system** that:
- 🔍 **Automatically scrapes** job listings from multiple sources (Remotive, We Work Remotely, Remote OK)
- 📊 **Displays jobs** in a beautiful live dashboard
- 🔔 **Sends macOS notifications** when new jobs are found
- 📝 **Tracks applications** with status updates
- 🔄 **Auto-refreshes** every 3 hours to find new opportunities

## ⚡ Quick Start (3 Steps)

### Step 1: Install Dependencies

Open Terminal in this folder and run:

```bash
pip3 install -r requirements.txt
```

This installs: Flask, BeautifulSoup4, Requests, and other required packages.

### Step 2: Scrape Initial Jobs

Run your first scrape to populate the database:

```bash
python3 job_scraper.py scrape
```

You'll see jobs being scraped and get a macOS notification when complete!

### Step 3: Start the Dashboard

Start the web server:

```bash
./start_server.sh
```

Or manually:

```bash
python3 api_server.py
```

Then open your browser to: **http://localhost:5000**

## 🎯 Using the Dashboard

### Main Features:

1. **🔄 Scrape Jobs Now Button** - Manually trigger a new scrape at any time
2. **🔍 Search Bar** - Search by company, title, or keywords
3. **📍 Location Filters** - Filter by Dubai, Netherlands, Germany, or Remote
4. **📊 Statistics** - See total jobs, tracked jobs, applications, and interviews
5. **Track This Button** - Add any job to your personal tracker
6. **Job Cards** - Click to view full job details

### Tracking Jobs:

- Click **"Track This"** on any job to add it to your tracker
- Update status: New → Applied → Interview → Offer/Rejected
- View all tracked jobs in the right sidebar
- Click "View" to open the original job posting

## 🤖 Automated Scraping (Optional)

To automatically scrape jobs every 3 hours:

```bash
chmod +x auto_scraper.sh setup_auto_scraper.sh
./setup_auto_scraper.sh
```

This will:
- Run the scraper every 3 hours automatically
- Send you notifications when new jobs are found
- Keep your job database fresh

### Disable Auto-Scraping:

```bash
launchctl unload ~/Library/LaunchAgents/com.jobtracker.scraper.plist
```

### Re-enable Auto-Scraping:

```bash
launchctl load ~/Library/LaunchAgents/com.jobtracker.scraper.plist
```

## 📡 Job Sources

The scraper automatically fetches from:

1. **Remotive** - Remote jobs API (worldwide)
2. **We Work Remotely** - Top remote job board
3. **Remote OK** - Digital nomad jobs

All these sources have jobs for:
- Dubai / UAE
- Netherlands
- Germany
- Remote (Worldwide/Europe)

## 💻 Command Line Usage

### Scrape Jobs:
```bash
python3 job_scraper.py scrape
```

### List Scraped Jobs:
```bash
python3 job_scraper.py list
```

### Start API Server:
```bash
python3 api_server.py
```

## 📁 Files Overview

- `live_dashboard.html` - Main web dashboard (opens via Flask server)
- `api_server.py` - Flask backend API server
- `job_scraper.py` - Web scraping logic
- `scraped_jobs.json` - Database of all scraped jobs
- `job_tracker.json` - Your tracked/applied jobs
- `last_scrape.json` - Timestamp of last scrape
- `requirements.txt` - Python dependencies
- `start_server.sh` - Quick start script
- `auto_scraper.sh` - Automated scraping script
- `setup_auto_scraper.sh` - Setup automated scraping

## 🔔 Notifications

You'll receive macOS notifications for:
- ✅ When new jobs are scraped
- 📝 When you track a new job
- 🔄 When automated scraping completes

Make sure to allow notifications when prompted!

## 🛠️ Troubleshooting

### "Cannot connect to server" error in dashboard

Make sure the API server is running:
```bash
python3 api_server.py
```

### No jobs showing after scraping

Check the scraper logs:
```bash
python3 job_scraper.py scrape
```

### Dependencies not installed

Install them:
```bash
pip3 install -r requirements.txt
```

### Automated scraping not working

Check if the job is loaded:
```bash
launchctl list | grep jobtracker
```

View logs:
```bash
cat scraper.log
```

## 🎨 Customization

### Change Scraping Frequency

Edit `setup_auto_scraper.sh` and modify the `StartInterval` value (in seconds):
- 3600 = 1 hour
- 10800 = 3 hours (default)
- 21600 = 6 hours

### Add More Job Sources

Edit `job_scraper.py` and add new scraping functions following the existing pattern.

### Change Dashboard Port

Edit `api_server.py` and change the port number in:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

## 📈 Tips for Success

1. **Run the scraper 2-3 times daily** for best results
2. **Track every interesting job** - you can always remove them later
3. **Update statuses promptly** to stay organized
4. **Use search** to find specific technologies or companies
5. **Enable notifications** to never miss new opportunities

## 🚀 Next Steps

1. ✅ Install dependencies
2. ✅ Scrape initial jobs
3. ✅ Start the dashboard
4. ✅ Setup automated scraping
5. ✅ Start applying!

## 💡 Pro Tips

- Keep the dashboard open in a browser tab
- Check it twice daily (morning and afternoon)
- Set up automated scraping to run in the background
- Use the search to find jobs matching your tech stack
- Track jobs even if you're not ready to apply yet

---

**Good luck with your job search!** 🎉

*Created with Claude Code*
