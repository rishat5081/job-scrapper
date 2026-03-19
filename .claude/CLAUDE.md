# JobIntel - Project Context for AI Agents

## Architecture

JobIntel is a Flask-based Python application using a `src/` layout. All source code lives in `src/jobintel/`.

### Module Map

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| `__init__.py` | Package root | `PROJECT_ROOT`, `DATA_DIR`, `TEMPLATES_DIR`, `__version__` |
| `api_server.py` | Flask REST API (20+ endpoints) | `app` |
| `job_scraper.py` | Multi-platform job scraping + filters | `scrape_all_jobs`, `filter_jobs`, `SCRAPERS` |
| `source_registry.py` | Source definitions + compliance metadata | `list_sources`, `get_source`, `SOURCE_DEFINITIONS` |
| `resume_pipeline.py` | Resume parsing, matching, tailoring | `build_resume_profile`, `match_jobs_to_profile`, `tailor_resume_for_job` |
| `pdf_utils.py` | PDF generation (Chrome headless + fallback) | `write_resume_pdf` |
| `job_monitor.py` | macOS job monitoring + notifications | Standalone script |

### Import Chain

```
api_server → job_scraper → source_registry
api_server → resume_pipeline → pdf_utils
api_server → source_registry
job_monitor (standalone)
```

### Data Flow

```
Source Registry → Job Scraper → scraped_jobs.json → API Server → Dashboard
                                                  ↕
                               Resume Pipeline → data/generated_resumes/
```

## Key Paths

- **Source code**: `src/jobintel/`
- **Tests**: `tests/`
- **Templates**: `templates/` (HTML dashboard files)
- **Scripts**: `scripts/` (shell scripts, automation)
- **Docs**: `docs/`
- **Runtime data**: `data/` (gitignored)
- **Config**: `pyproject.toml` (ruff, pytest, coverage, mypy, bandit)

## How to Run

```bash
# Tests (pythonpath configured in pyproject.toml)
python -m pytest tests/ -v

# Lint
ruff check src/ tests/
ruff format --check src/ tests/

# Server
PYTHONPATH=src python -m jobintel.api_server
# or: ./scripts/start_server.sh

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

## API Endpoints (Key)

- `GET /` → serves `templates/live_dashboard.html`
- `POST /api/scrape` → triggers all enabled scrapers
- `GET /api/scraped-jobs?search=...&page=1` → paginated job list
- `POST /api/profile/upload` → upload + parse resume
- `GET /api/matches` → jobs ranked by profile match
- `POST /api/jobs/:id/tailor` → generate tailored resume

## CI/CD

7 GitHub Actions workflows in `.github/workflows/`:
- `ci.yml` — pytest on Python 3.11/3.12 with `PYTHONPATH=src`
- `lint.yml` — ruff check/format, HTML validation, JS lint
- `security.yml` — pip-audit, bandit on `src/`, detect-secrets
- `codeql.yml` — GitHub CodeQL for Python
- `dependency-review.yml` — PR dependency check
- `release.yml` — changelog on tag push
- `stale.yml` — stale issue management
