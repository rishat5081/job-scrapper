# System Overview

## Runtime Shape

```text
Browser Dashboard
    ->
Flask API (src/jobintel/api_server.py)
    ->
Scraper (src/jobintel/job_scraper.py)
Resume Pipeline (src/jobintel/resume_pipeline.py)
Application Materials (src/jobintel/application_materials.py)
Application Autofill (src/jobintel/application_autofill.py)
PDF Renderer (src/jobintel/pdf_utils.py)
    ->
Runtime Data (data/)
```

## Main Components

### API

- Serves `templates/live_dashboard.html`
- Exposes scrape, profile upload, matching, pagination, and generation endpoints
- Provides application lifecycle endpoints (status, autofill, tracker)
- Runs on `http://localhost:8080`

### Scraper

- Executes enabled sources from `source_registry.py`
- Normalizes job payloads into one schema (tags flattened, locations normalized)
- Deduplicates and merges into `scraped_jobs.json`
- Records per-source status in `last_scrape.json`
- Enforces per-source timeouts via multiprocessing so one connector cannot stall the batch

### Resume Pipeline

- Parses and structures the uploaded resume
- Extracts job keywords with noise filtering and alias normalization
- Scores jobs against the profile with adjacent skill evidence
- Builds truthful tailored resumes (multi-attempt validation loop, up to 5 iterations)
- Validates output against evidenced job keywords
- Writes PDFs into `data/generated_resumes/`

### Application Materials

- Generates context-aware cover letters using job focus terms and profile evidence
- Creates draft interview answers (5 standard questions)
- Builds autofill payloads with field mapping for ATS forms
- Validates complete application packets with combined scoring
- Tracks application status through lifecycle: `prepared` > `ready_to_review` > `applied` > `interview` > `offer` / `rejected` / `archived`

### Application Autofill

- Launches Selenium WebDriver sessions to fill job application forms
- Auto-detects ATS provider from URL (Greenhouse, Lever, Workday, Ashby, Workable, BambooHR)
- Matches form fields to payload via name, id, placeholder, aria-label attributes
- Supports resume file upload
- Runs headless on Linux, detached on macOS/Windows

### Daily Task Runner

Implemented in:
- `scripts/run_today_tasks.py`

Responsibilities:
- Scrape or reuse the current snapshot
- Select today's batch
- Filter for relevant engineering roles
- Apply a minimum match threshold
- Generate tailored resumes and application packets
- Record pass/review outcomes
- Write JSON and Markdown reports

## Data Files

- `scraped_jobs.json` - merged job database
- `last_scrape.json` - latest scrape report and source statuses
- `data/resume_profile.json` - parsed resume profile
- `data/tailored_resumes.json` - artifact registry (resumes + packets)
- `data/application_tracker.json` - application status tracking
- `data/generated_resumes/*.pdf` - tailored resumes
- `data/generated_resumes/*_cover_letter.{pdf,md}` - cover letters
- `data/generated_resumes/*_draft_answers.{md,json}` - draft interview answers
- `data/reports/today_tasks_YYYY-MM-DD.{json,md}` - daily run reports

## Recommended Operator Loop

1. Start the server (`./start.sh`)
2. Confirm health (`curl http://localhost:8080/api/health`)
3. Run the daily task pipeline
4. Review the Markdown report
5. Inspect the PDFs and cover letters for passed jobs
6. Use autofill to pre-fill application forms
7. Update application status as you apply
8. Tune thresholds or tailoring logic if the report shows review failures
