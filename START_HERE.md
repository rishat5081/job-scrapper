# 🎯 START HERE - Job Tracker with Web Scraping

## What You Have

A **fully automated job search system** that:

✅ **Scrapes jobs** from Remotive, We Work Remotely, and Remote OK
✅ **Filters** for senior software engineering positions
✅ **Focuses** on Dubai, Netherlands, Germany, and Remote jobs
✅ **Displays** everything in a beautiful web dashboard
✅ **Notifies** you on macOS when new jobs are found
✅ **Tracks** your applications with status updates
✅ **Automates** scraping every 3 hours (optional)

---

## 🚀 Installation (One Command)

Open Terminal in this folder and run:

```bash
./install.sh
```

This will:
1. Create Python virtual environment
2. Install all dependencies
3. Scrape your first batch of jobs
4. Set everything up

**Time:** ~2-3 minutes

---

## 🎮 How to Use

### Start the Dashboard

```bash
./start_server.sh
```

Then open in your browser:
```
http://localhost:5000
```

### What You'll See

**Left Side - Available Jobs:**
- All scraped jobs from multiple sources
- Search by company, title, or keywords
- Filter by location
- Click "Track This" to add to your tracker
- Click cards to view full details

**Right Side - Your Tracked Jobs:**
- Jobs you're interested in or applied to
- Update status with one click
- Add notes for each position
- See application timeline

**Top Bar:**
- Click "Scrape Jobs Now" to get fresh listings
- See when jobs were last updated
- View statistics (total jobs, applied, interviews)

---

## 📋 Typical Workflow

### First Time Setup:
1. Run `./install.sh`
2. Run `./start_server.sh`
3. Open `http://localhost:5000`
4. Enable browser notifications
5. Browse available jobs
6. Click "Track This" on interesting positions

### Daily Use:
1. Open dashboard: `http://localhost:5000`
2. Click "🔄 Scrape Jobs Now"
3. Browse new listings
4. Track interesting jobs
5. Apply to positions
6. Update application statuses

---

## 🔄 Automated Scraping (Optional)

Want jobs scraped automatically every 3 hours?

```bash
./setup_auto_scraper.sh
```

This runs in the background. You'll get notified when new jobs are found.

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `install.sh` | One-command installation |
| `start_server.sh` | Start the dashboard |
| `setup_auto_scraper.sh` | Setup automated scraping |
| `README_SCRAPER.md` | Full documentation |
| `SETUP_GUIDE.md` | Detailed setup guide |

---

## 🔍 Job Sources

Your system automatically scrapes from:

1. **Remotive** - Top remote jobs aggregator
   - API-based, very reliable
   - Worldwide remote positions

2. **We Work Remotely** - #1 remote job board
   - High-quality listings
   - Startup-focused

3. **Remote OK** - Digital nomad jobs
   - Salary information included
   - Wide geographic coverage

All filtered for:
- ✅ Senior software engineering roles
- ✅ Dubai, Netherlands, Germany locations
- ✅ Remote (worldwide/Europe) positions

---

## 🔔 Notifications

You'll receive macOS notifications for:

- 📢 New jobs found during scraping
- 📝 Jobs added to your tracker
- ✅ Scraping completed

Make sure to **allow notifications** when prompted!

---

## 💡 Pro Tips

1. **Scrape 2-3 times daily** for best coverage
2. **Track liberally** - it's easy to remove jobs later
3. **Update statuses promptly** - stay organized
4. **Use search** to find your tech stack
5. **Set up auto-scraping** - hands-off job discovery
6. **Check dashboard daily** - make it a routine

---

## ❓ Quick Troubleshooting

### Dashboard won't load
```bash
./start_server.sh
```
Make sure it's running, then try `http://localhost:5000`

### No jobs showing
```bash
source venv/bin/activate
python job_scraper.py scrape
```
Manually trigger a scrape

### Need to reinstall
```bash
rm -rf venv
./install.sh
```

---

## 📊 What to Expect

**First Scrape:**
- 30-60 senior software engineering jobs

**Daily New Jobs:**
- 5-15 new positions per day

**Response Rate:**
- Track 10-15 jobs per week
- Apply to 5-10 positions per week

---

## 🎯 Next Steps

1. ✅ Run `./install.sh` (if not done yet)
2. ✅ Run `./start_server.sh`
3. ✅ Open `http://localhost:5000`
4. ✅ Click "Scrape Jobs Now"
5. ✅ Start tracking jobs!
6. ✅ Optional: Run `./setup_auto_scraper.sh`

---

## 📖 Documentation

- **START_HERE.md** ← You are here
- **README_SCRAPER.md** - Complete documentation
- **SETUP_GUIDE.md** - Detailed setup instructions

---

## ✅ Quick Checklist

- [ ] Ran `./install.sh`
- [ ] Started dashboard with `./start_server.sh`
- [ ] Opened `http://localhost:5000` in browser
- [ ] Enabled notifications
- [ ] Scraped first batch of jobs
- [ ] Tracked at least one job
- [ ] Set up automated scraping (optional)

---

**Ready to find your dream senior software engineering job!** 🚀

*Questions? Check README_SCRAPER.md for detailed docs.*
