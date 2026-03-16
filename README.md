# Job Intelligence System

This repo is now a governed job-ingestion and resume-tailoring system.

It does five things:

1. Keeps a source catalog of major job boards and marks which ones are safe to automate in this repo.
2. Ingests jobs from enabled connectors.
3. Uploads and parses a resume into a reusable candidate profile.
4. Scores each job against that profile and generates a tailored resume.
5. Validates the tailored resume and exports it as a PDF artifact.

## What Changed

The previous codebase was a lightweight tracker. The current system adds:

- `source_registry.py`: source catalog and compliance metadata
- `job_scraper.py`: governed ingestion from enabled sources
- `resume_pipeline.py`: resume parsing, matching, tailoring, validation, artifact storage
- `pdf_utils.py`: PDF generation without extra dependencies
- `api_server.py`: API for upload, scraping, matching, tailoring, download
- `live_dashboard.html`: workflow UI for sources, resume upload, matched jobs, and generated PDFs

## Current Source Policy

Automated by default:

- Remotive
- We Work Remotely
- Remote OK

Listed but not automatically scraped in this repo by default:

- LinkedIn
- Indeed
- Glassdoor
- Wellfound
- Bayt
- NaukriGulf
- No Fluff Jobs
- Just Join IT

Those boards remain visible in the catalog so the system can be extended later with approved feeds, official APIs, or manual-review workflows.

## Run It

Start the API and dashboard:

```bash
venv/bin/python api_server.py
```

Open:

- Dashboard: [http://localhost:8080](http://localhost:8080)

## Main API Endpoints

- `GET /api/health`
- `GET /api/sources`
- `GET /api/profile`
- `POST /api/profile/upload`
- `GET /api/scraped-jobs`
- `POST /api/scrape`
- `GET /api/matches`
- `POST /api/jobs/<job_id>/tailor`
- `POST /api/pipeline/run`
- `GET /api/generated-resumes`
- `GET /api/generated-resumes/<filename>`
- `GET /api/stats`

## Resume Intake Notes

Best-effort extraction currently supports:

- `txt`
- `md`
- `doc`
- `docx`
- `rtf`
- `odt`
- `pdf`

`pdf` extraction uses text fallback only, so the cleanest results still come from text-based or office-document resumes.

## Validation Rules

The tailoring engine does not invent unsupported claims. If a job description asks for skills not evidenced in the uploaded resume, the validator flags them as unsupported instead of fabricating them.

## Tests

Run:

```bash
venv/bin/python -m unittest discover -s tests
```
