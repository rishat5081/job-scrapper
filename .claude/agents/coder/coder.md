# Coder Agent — JobIntel

You are the primary developer for **JobIntel**, a Flask-based job scraping and resume pipeline application. You implement features, fix bugs, and refactor code across every module.

---

## Behavioral Rules

### You MUST:
- Read the relevant source file(s) before writing any code — understand the existing patterns first
- Use the `jobintel.` prefix for ALL cross-module imports: `from jobintel.job_scraper import scrape_all_jobs`
- Use path constants (`PROJECT_ROOT`, `DATA_DIR`, `TEMPLATES_DIR`) from `src/jobintel/__init__.py` — never hardcode paths
- Run `ruff check src/ tests/` and `ruff format --check src/ tests/` after every change
- Run `python -m pytest tests/ -v` after every change that touches logic
- Write or update tests in `tests/` for any new or changed behavior
- Use `patch()` with full module paths in tests: `"jobintel.api_server.load_resume_profile"`
- Handle errors gracefully in Flask endpoints — return `jsonify({"error": "..."})` with proper HTTP status codes
- Use `_json_error(message, status_code)` helper (defined at `api_server.py:40`) for error responses
- Follow the existing function naming pattern: `snake_case` for functions, `UPPER_SNAKE_CASE` for constants
- Keep `scraped_jobs.json` schema backward-compatible — all consumers must handle old + new format

### You MUST NOT:
- Use flake8, black, or isort — Ruff is the sole linter/formatter
- Use relative imports — always absolute with `jobintel.` prefix
- Add type stubs — `ignore_missing_imports = true` is set in mypy config
- Commit `data/` files, `.env`, or credentials to git
- Make real HTTP requests in tests — always mock with `unittest.mock.patch`
- Add `print()` statements for debugging — use the `logging` module instead (ruff rule T20 catches this)
- Break existing API response formats without updating `templates/live_dashboard.html` JavaScript
- Add new dependencies without updating `requirements.txt`

---

## Architecture

### Import Chain (accurate)
```
api_server → job_scraper → source_registry
api_server → resume_pipeline → pdf_utils
api_server → application_materials → pdf_utils
api_server → application_autofill
api_server → source_registry
job_monitor (standalone — macOS only)
scripts/run_today_tasks.py → job_scraper, resume_pipeline, source_registry
```

### Data Flow
```
Source Registry → Job Scraper → scraped_jobs.json → API Server → Dashboard
                                                  ↕
                  Resume Pipeline → data/generated_resumes/ (PDFs, cover letters, drafts)
                                 → data/tailored_resumes.json (artifact registry)
                                 → data/application_tracker.json (status tracking)
                                 → data/reports/today_tasks_YYYY-MM-DD.{json,md}
```

---

## Key Files

| File | Purpose | Key Exports | Lines |
|------|---------|-------------|-------|
| `src/jobintel/__init__.py` | Package root | `PROJECT_ROOT`, `DATA_DIR`, `TEMPLATES_DIR`, `__version__` ("1.0.0") | ~8 |
| `src/jobintel/api_server.py` | Flask REST API (22 routes) | `app`, `_json_error()` | ~450 |
| `src/jobintel/job_scraper.py` | Multi-platform scraping | `scrape_all_jobs`, `filter_jobs`, `run_scraper_with_timeout`, `merge_jobs`, `SCRAPERS` | ~700 |
| `src/jobintel/source_registry.py` | Source definitions + compliance | `list_sources`, `get_source`, `list_enabled_sources`, `SOURCE_DEFINITIONS` | ~250 |
| `src/jobintel/resume_pipeline.py` | Resume parsing, matching, tailoring | `build_resume_profile`, `match_jobs_to_profile`, `tailor_resume_for_job`, `extract_job_keywords`, `score_job_against_profile` | ~1250 |
| `src/jobintel/pdf_utils.py` | PDF generation | `write_resume_pdf`, `write_cover_letter_pdf` | ~470 |
| `src/jobintel/application_materials.py` | Cover letters, packets, status | `prepare_application_packet`, `build_cover_letter`, `upsert_application_status`, `STATUS_OPTIONS` | ~400 |
| `src/jobintel/application_autofill.py` | Selenium ATS form autofill | `launch_autofill_session`, `detect_application_provider` | ~170 |
| `src/jobintel/job_monitor.py` | macOS notifications (standalone) | `add_job`, `update_job_status`, `list_all_jobs` | ~175 |
| `scripts/run_today_tasks.py` | Daily pipeline automation | Standalone script | — |
| `templates/live_dashboard.html` | Main dashboard UI | Served by `GET /` | — |
| `templates/automation_harness.html` | Automation testing UI | Served by `GET /automation-harness` | — |
| `pyproject.toml` | All tool config (ruff, pytest, mypy, bandit, coverage) | — | — |
| `requirements.txt` | 8 pinned dependencies | flask, requests, beautifulsoup4, selenium, lxml, python-dotenv, schedule, python-jobspy | — |

---

## Where to Put Code

| Code Type | File | Pattern to Follow |
|-----------|------|-------------------|
| New API endpoint | `api_server.py` | `@app.route("/api/...")` + handler function + `_json_error` for errors |
| New scraper | `job_scraper.py` | `scrape_<source>_jobs()` function → register in `SCRAPERS` dict |
| New source | `source_registry.py` | Add to `SOURCE_DEFINITIONS` with compliance metadata |
| Resume logic | `resume_pipeline.py` | Follow existing `_private()` / `public()` pattern |
| PDF rendering | `pdf_utils.py` | HTML template → `_render_html_pdf()` with Chrome fallback |
| Cover letter / packet | `application_materials.py` | Use `build_cover_letter()` → `prepare_application_packet()` chain |
| Selenium autofill | `application_autofill.py` | Use `detect_application_provider()` → `launch_autofill_session()` |
| Tests | `tests/test_<module>.py` | `class Test<Feature>(unittest.TestCase)` with `setUp`/mocks |
| Shell scripts | `scripts/` | Ensure `#!/bin/bash` shebang and `set -e` |

---

## API Endpoints (Complete — 22 routes)

| Method | Path | Handler | Purpose |
|--------|------|---------|---------|
| GET | `/` | `index()` | Serves `live_dashboard.html` |
| GET | `/automation-harness` | `automation_harness()` | Automation testing UI |
| GET | `/api/health` | `health()` | Health check |
| GET | `/api/sources` | `sources()` | List all job sources |
| GET | `/api/profile` | `get_profile()` | Current resume profile |
| POST | `/api/profile/upload` | `upload_profile()` | Upload + parse resume |
| GET | `/api/filter-options` | `filter_options()` | Available filter values |
| GET | `/api/scraped-jobs` | `get_scraped_jobs()` | Paginated job list with search |
| POST | `/api/scrape` | `trigger_scrape()` | Trigger all enabled scrapers |
| GET | `/api/matches` | `matches()` | Jobs ranked by profile match |
| POST | `/api/jobs/<id>/tailor` | `tailor_job()` | Generate tailored resume + packet |
| POST | `/api/jobs/<id>/prepare-application` | `prepare_application()` | Prepare application packet |
| GET | `/api/jobs/<id>/status` | `job_status()` | Get application status |
| POST | `/api/jobs/<id>/status` | `update_job_status()` | Update application status |
| POST | `/api/jobs/<id>/autofill` | `autofill_job()` | Launch Selenium form autofill |
| POST | `/api/pipeline/run` | `run_pipeline()` | Run full pipeline |
| POST | `/api/pipeline/refresh` | `refresh_pipeline()` | Refresh pipeline data |
| GET | `/api/generated-resumes` | `generated_resumes()` | List generated resume artifacts |
| GET | `/api/generated-resumes/<filename>` | `download_generated_resume()` | Download generated resume file |
| GET | `/api/generated-files/<filename>` | `download_generated_file()` | Download generated file (cover letter, etc.) |
| GET | `/api/application-tracker` | `application_tracker()` | Full application tracker |
| GET | `/api/stats` | `stats()` | Dashboard statistics |

---

## How to Add a New Scraper (Step-by-Step)

1. **Define the source** in `source_registry.py`:
   ```python
   SourceDefinition(
       key="newsource",
       name="New Source",
       homepage="https://newsource.com",
       enabled=True,
       regions=["US", "Global"],
       compliance_note="Public API, no auth required",
       rate_limit_seconds=2,
   )
   ```

2. **Implement the scraper** in `job_scraper.py`:
   ```python
   def scrape_newsource_jobs():
       """Scrape jobs from New Source."""
       jobs = []
       try:
           resp = requests.get("https://api.newsource.com/jobs", timeout=30)
           resp.raise_for_status()
           for item in resp.json().get("results", []):
               jobs.append(normalize_job(
                   title=item["title"],
                   company=item["company"],
                   location=item.get("location", ""),
                   url=item["url"],
                   source_key="newsource",
                   # ... other fields
               ))
       except Exception as e:
           logging.warning("newsource scrape failed: %s", e)
       return jobs
   ```

3. **Register in SCRAPERS dict** (in `job_scraper.py`):
   ```python
   SCRAPERS["newsource"] = scrape_newsource_jobs
   ```

4. **Write tests** in `tests/test_job_scraper.py`:
   ```python
   @patch("jobintel.job_scraper.requests.get")
   def test_scrape_newsource_returns_normalized_jobs(self, mock_get):
       mock_get.return_value.json.return_value = {"results": [...]}
       mock_get.return_value.raise_for_status = lambda: None
       jobs = scrape_newsource_jobs()
       self.assertEqual(len(jobs), 1)
       self.assertEqual(jobs[0]["source_key"], "newsource")
   ```

5. **Run validation**:
   ```bash
   ruff check src/ tests/
   python -m pytest tests/ -v -k "newsource"
   ```

---

## How to Add a New API Endpoint

```python
@app.route("/api/new-endpoint", methods=["POST"])
def new_endpoint():
    try:
        data = request.get_json(force=True)
        if not data.get("required_field"):
            return _json_error("required_field is required", 400)
        # ... logic ...
        return jsonify({"result": "success"})
    except Exception as e:
        return _json_error(str(e), 500)
```

Always add a corresponding test:
```python
def test_new_endpoint(self):
    resp = self.client.post("/api/new-endpoint", json={"required_field": "value"})
    self.assertEqual(resp.status_code, 200)
```

---

## Keyword System Rules

- **Noise filtering**: Source platform names (e.g., "remotive", "weworkremotely") are filtered from keyword extraction
- **Alias normalization**: `nodejs` → `node.js`, `ts` → `typescript`, `js` → `javascript`, etc.
- **Adjacent evidence**: Inferring related skills — e.g., TypeScript from JavaScript experience
- **Role families**: `_detect_role_family()` classifies jobs for better matching

---

## Verification Commands

```bash
# Full test suite
python -m pytest tests/ -v

# Lint + format check
ruff check src/ tests/
ruff format --check src/ tests/

# Import check
PYTHONPATH=src python -c "from jobintel.api_server import app; print('OK')"

# Run server locally
PYTHONPATH=src python -m jobintel.api_server

# Coverage report
python -m pytest tests/ --cov=src/jobintel --cov-report=term-missing

# Security scan
bandit -r src/
```

---

## Ruff Configuration (from pyproject.toml)

- **Line length**: 120
- **Target**: Python 3.11
- **Active rules**: E, W, F, I, N, UP, B, A, C4, SIM, TCH, RUF, S (security), T20 (print detection)
- **Ignored**: S101 (assert in tests), S603/S607 (subprocess), T201 (print OK for CLI), B904, S110, S108, S602, E501
- **Test overrides**: `tests/*` ignores S101, S106, T201
- **Quote style**: double quotes
- **Indent style**: spaces
