# Start Here

## The Short Version

1. Start the app:

```bash
cd /Users/user/Desktop/Work/jobs
./start.sh
```

2. Open:
- `http://localhost:8080`

3. Upload your resume if the profile is not already loaded.

4. Run the daily task pipeline:

```bash
cd /Users/user/Desktop/Work/jobs
PYTHONPATH=src venv/bin/python scripts/run_today_tasks.py \
  --allow-scraped-today-fallback \
  --min-match-score 90 \
  --min-validation-score 70
```

5. Review:
- `data/reports/today_tasks_YYYY-MM-DD.md` (summary report)
- `data/generated_resumes/*.pdf` (tailored resumes)
- `data/generated_resumes/*_cover_letter.pdf` (cover letters)
- `data/generated_resumes/*_draft_answers.md` (interview prep)

6. Apply:
- Use autofill: `POST /api/jobs/JOB_ID/autofill`
- Track status: `POST /api/jobs/JOB_ID/status` with `{"status": "applied"}`
- View tracker: `GET /api/application-tracker`

## What "Done" Looks Like

- App is serving on `8080`
- Job sources scraped without hanging (per-source timeouts enforced)
- Today's relevant engineering jobs identified
- Tailored PDFs generated with cover letters and draft answers
- Validation scores recorded (resume + packet combined)
- One Markdown report and one JSON report written for the run
- Application status tracked for each job
