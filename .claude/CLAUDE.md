# JobIntel - Project Context for AI Agents

## Architecture

JobIntel is a Flask-based Python application using a `src/` layout. All source code lives in `src/jobintel/`.

### Module Map

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| `__init__.py` | Package root | `PROJECT_ROOT`, `DATA_DIR`, `TEMPLATES_DIR`, `__version__` |
| `api_server.py` | Flask REST API (25+ endpoints) | `app` |
| `job_scraper.py` | Multi-platform job scraping + filters + timeouts | `scrape_all_jobs`, `filter_jobs`, `SCRAPERS`, `run_scraper_with_timeout` |
| `source_registry.py` | Source definitions + compliance metadata | `list_sources`, `get_source`, `SOURCE_DEFINITIONS` |
| `resume_pipeline.py` | Resume parsing, matching, tailoring, validation | `build_resume_profile`, `match_jobs_to_profile`, `tailor_resume_for_job`, `extract_job_keywords` |
| `pdf_utils.py` | PDF generation (Chrome headless + fallback) | `write_resume_pdf`, `write_cover_letter_pdf` |
| `application_materials.py` | Cover letters, draft answers, packet validation, status tracking | `prepare_application_packet`, `build_cover_letter`, `upsert_application_status`, `STATUS_OPTIONS` |
| `application_autofill.py` | Selenium ATS form autofill + provider detection | `launch_autofill_session`, `detect_application_provider` |
| `job_monitor.py` | macOS job monitoring + notifications | Standalone script |

### Import Chain

```
api_server → job_scraper → source_registry
api_server → resume_pipeline → pdf_utils
                             → application_materials → pdf_utils
api_server → application_materials (status tracking)
api_server → application_autofill (Selenium autofill)
api_server → source_registry
job_monitor (standalone)
scripts/run_today_tasks.py → job_scraper, resume_pipeline, source_registry
```

### Data Flow

```
Source Registry → Job Scraper → scraped_jobs.json → API Server → Dashboard
                                                  ↕
                     Resume Pipeline → data/generated_resumes/ (PDFs, cover letters, drafts)
                                    → data/tailored_resumes.json (artifact registry)
                                    → data/application_tracker.json (status tracking)
                                    → data/reports/ (daily JSON + Markdown reports)
```

## Key Paths

- **Source code**: `src/jobintel/`
- **Tests**: `tests/`
- **Templates**: `templates/` (HTML dashboard files)
- **Scripts**: `scripts/` (shell scripts, daily runner)
- **Docs**: `docs/`
- **Runtime data**: `data/` (gitignored)
- **Config**: `pyproject.toml` (ruff, pytest, coverage, mypy, bandit)
- **Bootstrap**: `start.sh` (cross-platform setup + server start)

## How to Run

```bash
# Bootstrap everything (cross-platform)
./start.sh

# Tests (pythonpath configured in pyproject.toml)
python -m pytest tests/ -v

# Lint
ruff check src/ tests/
ruff format --check src/ tests/

# Server
PYTHONPATH=src python -m jobintel.api_server
# or: ./scripts/start_server.sh

# Daily pipeline
PYTHONPATH=src python scripts/run_today_tasks.py --allow-scraped-today-fallback

# Import check
PYTHONPATH=src python -c "from jobintel.api_server import app; print('OK')"
```

## Conventions

- All cross-module imports use `jobintel.` prefix (e.g., `from jobintel.job_scraper import ...`)
- Path constants (`PROJECT_ROOT`, `DATA_DIR`, `TEMPLATES_DIR`) are defined in `src/jobintel/__init__.py`
- Tests use `pytest` with `pythonpath = ["src"]` in `pyproject.toml`
- `patch()` targets use full module paths: `"jobintel.api_server.load_resume_profile"`
- Ruff is the sole linter/formatter (no flake8, black, isort)
- No type stubs required (`ignore_missing_imports = true`)
- Noise keywords (source platform names) are filtered from job keyword extraction
- Keyword aliases normalize variants (`nodejs` -> `node.js`, `ts` -> `typescript`)
- Adjacent evidence allows inferring related skills (TypeScript from JavaScript)

## API Endpoints (Key)

- `GET /` -> serves `templates/live_dashboard.html`
- `POST /api/scrape` -> triggers all enabled scrapers with per-source timeouts
- `GET /api/scraped-jobs?search=...&page=1` -> paginated job list
- `POST /api/profile/upload` -> upload + parse resume
- `GET /api/matches` -> jobs ranked by profile match
- `POST /api/jobs/:id/tailor` -> generate tailored resume + application packet
- `POST /api/jobs/:id/autofill` -> launch Selenium form autofill
- `GET/POST /api/jobs/:id/status` -> application status tracking
- `GET /api/application-tracker` -> full tracker across all jobs
- `GET /api/generated-files/:filename` -> download cover letters, draft answers

## Data Files

- `scraped_jobs.json` - merged job database
- `last_scrape.json` - latest scrape report with source statuses
- `data/resume_profile.json` - parsed resume profile
- `data/tailored_resumes.json` - artifact registry (resumes + packets)
- `data/application_tracker.json` - application status tracking
- `data/generated_resumes/` - PDFs, cover letters (.pdf/.md), draft answers (.md/.json)
- `data/reports/today_tasks_YYYY-MM-DD.{json,md}` - daily pipeline reports

## CI/CD

7 GitHub Actions workflows in `.github/workflows/`:
- `ci.yml` - pytest on Python 3.11/3.12 with `PYTHONPATH=src`
- `lint.yml` - ruff check/format, HTML validation, JS lint
- `security.yml` - pip-audit, bandit on `src/`, detect-secrets
- `codeql.yml` - GitHub CodeQL for Python
- `dependency-review.yml` - PR dependency check
- `release.yml` - changelog on tag push
- `stale.yml` - stale issue management
