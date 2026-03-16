# ⚡ Quick Reference Card

## 🚀 Installation (First Time Only)

```bash
cd /Users/user/Desktop/Work/jobs
./install.sh
```

---

## 🎮 Daily Commands

### Start Dashboard
```bash
./start_server.sh
```
Then open: **http://localhost:5000**

### Manual Scrape (Optional)
```bash
source venv/bin/activate
python job_scraper.py scrape
```

---

## 🔄 Setup Auto-Scraping (Once)

```bash
./setup_auto_scraper.sh
```
Jobs will be scraped every 3 hours automatically.

---

## 📊 Dashboard URL

**http://localhost:5000**

Bookmark this!

---

## 🔔 What You'll Get

- ✅ **30-60 jobs** on first scrape
- ✅ **5-15 new jobs** per day
- ✅ macOS notifications for new jobs
- ✅ Search & filter by location
- ✅ Track applications with status
- ✅ One-click job viewing

---

## 📍 Job Locations

- Dubai / UAE
- Netherlands
- Germany
- Remote (Worldwide/Europe)

---

## 🎯 Job Sources

1. **Remotive** - Remote jobs API
2. **We Work Remotely** - #1 remote board
3. **Remote OK** - Digital nomad jobs

---

## ⌨️ Keyboard Shortcuts

In Dashboard:
- Type in search box to filter jobs
- Click location tabs to filter
- Click "Track This" to save jobs

---

## 📂 Important Files

| File | Purpose |
|------|---------|
| `start_server.sh` | Start dashboard |
| `START_HERE.md` | Getting started guide |
| `README_SCRAPER.md` | Full documentation |
| `scraped_jobs.json` | All scraped jobs |
| `job_tracker.json` | Your applications |

---

## 🛠️ Troubleshooting

**Dashboard not loading?**
```bash
./start_server.sh
```

**No jobs appearing?**
```bash
source venv/bin/activate
python job_scraper.py scrape
```

**Need to reinstall?**
```bash
rm -rf venv
./install.sh
```

---

## ✅ Daily Checklist

- [ ] Open http://localhost:5000
- [ ] Click "Scrape Jobs Now"
- [ ] Browse new listings
- [ ] Track interesting positions
- [ ] Apply to 2-3 jobs
- [ ] Update application statuses

---

## 🎯 Weekly Goals

- Track: 10-15 jobs
- Apply: 5-10 jobs
- Interviews: 1-3 scheduled

---

**Keep this card handy!** 📌
