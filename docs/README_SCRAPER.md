# Scraping And Daily Operations

## What The Scraper Does

The app ingests jobs from the enabled sources in the source registry and merges them into `scraped_jobs.json`.

Enabled sources in the current build:
- Remotive
- We Work Remotely
- Remote OK
- LinkedIn
- Indeed
- Glassdoor
- Himalayas
- Jobicy

Important runtime behavior:
- Every source is executed in a separate process with a hard timeout
- Slow or blocked connectors are reported instead of hanging the full batch
- Duplicate jobs are merged by deterministic job ID
- Tags are flattened from nested structures and deduplicated
- Noise keywords (platform names like "linkedin", "jobspy") are filtered from extraction

## Current Daily Workflow

1. Load the saved resume profile from `data/resume_profile.json`
2. Scrape all enabled sources (with per-source timeouts)
3. Select jobs from today's batch
4. Filter to relevant software/backend/full-stack/devops/platform roles
5. Match those jobs against the resume profile (with adjacent skill evidence)
6. Generate tailored PDFs for the strongest matches
7. Generate cover letters and draft interview answers
8. Validate each tailored resume and application packet
9. Write JSON and Markdown reports under `data/reports/`

## Daily Command

```bash
cd /Users/user/Desktop/Work/jobs
PYTHONPATH=src venv/bin/python scripts/run_today_tasks.py \
  --allow-scraped-today-fallback \
  --min-match-score 90 \
  --min-validation-score 70
```

## Snapshot Re-Run

Use this after changing matching or resume logic, so you do not scrape again unnecessarily:

```bash
cd /Users/user/Desktop/Work/jobs
PYTHONPATH=src venv/bin/python scripts/run_today_tasks.py \
  --skip-scrape \
  --allow-scraped-today-fallback \
  --min-match-score 90 \
  --min-validation-score 70
```

## Output Files

- `scraped_jobs.json`: merged job database
- `last_scrape.json`: latest scrape report and source statuses
- `data/generated_resumes/*.pdf`: tailored resumes
- `data/generated_resumes/*_cover_letter.{pdf,md}`: cover letters
- `data/generated_resumes/*_draft_answers.{md,json}`: draft interview answers
- `data/tailored_resumes.json`: artifact registry
- `data/application_tracker.json`: application status tracking
- `data/reports/today_tasks_YYYY-MM-DD.json`: machine-readable run report
- `data/reports/today_tasks_YYYY-MM-DD.md`: operator summary

## Notes On "Today"

Not every source provides a reliable `date_posted` for the current day. The daily runner therefore supports two modes:
- strict today by `date_posted`
- fallback to `date_scraped` when explicit same-day posting data is unavailable

The report records which basis was used.
