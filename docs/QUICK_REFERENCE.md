# Quick Reference

## Start The App

```bash
cd /Users/user/Desktop/Work/jobs
./start.sh
```

Dashboard:
- `http://localhost:8080`

Health check:
```bash
curl http://127.0.0.1:8080/api/health
```

## Run The Daily Task Pipeline

```bash
cd /Users/user/Desktop/Work/jobs
PYTHONPATH=src venv/bin/python scripts/run_today_tasks.py \
  --allow-scraped-today-fallback \
  --min-match-score 90 \
  --min-validation-score 70
```

What it does:
- scrapes all enabled sources (with per-source timeouts)
- selects today's batch
- filters to relevant engineering roles
- matches jobs to the loaded resume profile
- generates tailored resume PDFs
- generates cover letters and draft interview answers
- validates each output (resume + packet combined)
- writes reports to `data/reports/`

## Re-Run Without Scraping

```bash
cd /Users/user/Desktop/Work/jobs
PYTHONPATH=src venv/bin/python scripts/run_today_tasks.py \
  --skip-scrape \
  --allow-scraped-today-fallback \
  --min-match-score 90 \
  --min-validation-score 70
```

## Test Commands

```bash
cd /Users/user/Desktop/Work/jobs
PYTHONPATH=src venv/bin/python -m pytest -q
python3 -m py_compile src/jobintel/*.py scripts/run_today_tasks.py
```

## Important Paths

- `src/jobintel/`: application package (9 modules)
- `templates/live_dashboard.html`: dashboard UI
- `scripts/run_today_tasks.py`: daily pipeline runner
- `data/resume_profile.json`: parsed resume profile
- `data/tailored_resumes.json`: artifact registry
- `data/application_tracker.json`: application status tracking
- `data/generated_resumes/`: tailored PDFs, cover letters, draft answers
- `data/reports/`: daily run reports

## Current Daily Report Format

- JSON: `data/reports/today_tasks_YYYY-MM-DD.json`
- Markdown: `data/reports/today_tasks_YYYY-MM-DD.md`

Each report includes:
- source-by-source scrape status
- how today's jobs were selected
- how many jobs were filtered out as non-relevant
- generated PDFs and validation results (resume + packet scores)
- items needing manual review

## Application Lifecycle

Status flow: `prepared` > `ready_to_review` > `applied` > `interview` > `offer` / `rejected` / `archived`

Update via API:
```bash
curl -X POST http://127.0.0.1:8080/api/jobs/JOB_ID/status \
  -H "Content-Type: application/json" \
  -d '{"status": "applied", "notes": "Applied on company website"}'
```

View tracker:
```bash
curl http://127.0.0.1:8080/api/application-tracker
```
