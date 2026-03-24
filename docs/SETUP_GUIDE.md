# Setup Guide

## 1. Install

### One-Command Bootstrap (Recommended)

```bash
cd /Users/user/Desktop/Work/jobs
./start.sh
```

This cross-platform script:
- Detects your OS (macOS, Linux, Windows)
- Installs system packages (Python 3.11+, Chrome for PDFs)
- Creates a virtual environment
- Installs Python dependencies
- Starts the Flask server

### Manual Install

```bash
cd /Users/user/Desktop/Work/jobs
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Start The Dashboard

```bash
./start.sh
# or: ./scripts/start_server.sh
# or: PYTHONPATH=src python -m jobintel.api_server
```

Then open:
- `http://localhost:8080`

## 3. Load A Resume

Use the dashboard upload flow or call the API:

```bash
curl -F "resume=@/path/to/resume.pdf" http://127.0.0.1:8080/api/profile/upload
```

Supported formats: txt, md, doc, docx, rtf, odt, pdf

The parsed profile is stored at:
- `data/resume_profile.json`

## 4. Run The Daily Pipeline

```bash
PYTHONPATH=src venv/bin/python scripts/run_today_tasks.py \
  --allow-scraped-today-fallback \
  --min-match-score 90 \
  --min-validation-score 70
```

This generates:
- Refreshed scrape data
- Ranked relevant jobs
- Tailored resume PDFs
- Cover letters and draft interview answers
- Validation results (resume + packet combined)
- Markdown and JSON reports

## 5. Application Workflow

After generating artifacts:

1. Review PDFs and cover letters in `data/generated_resumes/`
2. Use autofill to pre-fill application forms:
   ```bash
   curl -X POST http://127.0.0.1:8080/api/jobs/JOB_ID/autofill
   ```
3. Track application status:
   ```bash
   curl -X POST http://127.0.0.1:8080/api/jobs/JOB_ID/status \
     -H "Content-Type: application/json" \
     -d '{"status": "applied"}'
   ```

## 6. Verify

```bash
curl http://127.0.0.1:8080/api/health
PYTHONPATH=src venv/bin/python -m pytest -q
```

## Troubleshooting

Dashboard not responding:
```bash
curl http://127.0.0.1:8080/api/health
```

Need a report-only rerun after code changes:
```bash
PYTHONPATH=src venv/bin/python scripts/run_today_tasks.py \
  --skip-scrape \
  --allow-scraped-today-fallback \
  --min-match-score 90 \
  --min-validation-score 70
```

Need to inspect the latest run:
```bash
ls -lt data/reports
cat data/reports/today_tasks_$(date +%F).md
```

Chrome not found (PDF generation):
```bash
# macOS
brew install --cask google-chrome

# Linux
sudo apt install google-chrome-stable
```
