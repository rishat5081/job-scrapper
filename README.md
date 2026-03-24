<div align="center">

# JobIntel - Job Intelligence System

**AI-powered job scraping, resume matching, tailored resume generation, and application automation across 9 platforms.**

[![CI](https://github.com/rishat5081/job-scrapper/actions/workflows/ci.yml/badge.svg)](https://github.com/rishat5081/job-scrapper/actions/workflows/ci.yml)
[![Lint](https://github.com/rishat5081/job-scrapper/actions/workflows/lint.yml/badge.svg)](https://github.com/rishat5081/job-scrapper/actions/workflows/lint.yml)
[![Security](https://github.com/rishat5081/job-scrapper/actions/workflows/security.yml/badge.svg)](https://github.com/rishat5081/job-scrapper/actions/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB.svg)](https://www.python.org/)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

</div>

---

## Overview

JobIntel is a governed job ingestion and resume tailoring system that:

1. **Scrapes jobs** from 9 platforms (Remotive, WWR, RemoteOK, LinkedIn, Indeed, Glassdoor, Himalayas, Jobicy, Adzuna)
2. **Parses resumes** into structured candidate profiles via multi-format extraction
3. **Scores & ranks** each job against your profile using keyword overlap and role-family detection
4. **Generates tailored resumes** with validation, keyword optimization, and PDF export
5. **Prepares full application packets** with cover letters, draft interview answers, and autofill payloads
6. **Automates form filling** via Selenium with ATS provider detection (Greenhouse, Lever, Workday, etc.)
7. **Tracks application status** through the full lifecycle (prepared, applied, interview, offer)
8. **Serves a modern dashboard** with dark mode, advanced filters, and real-time previews

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (Dashboard)                    │
│   Sidebar Nav │ Stats │ Jobs Grid │ Filters │ Preview    │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP/JSON
┌──────────────────────────▼──────────────────────────────┐
│               Flask API (api_server.py)                   │
│  /api/scrape │ /api/scraped-jobs │ /api/profile/upload    │
│  /api/matches │ /api/jobs/:id/tailor │ /api/filter-options│
│  /api/jobs/:id/autofill │ /api/application-tracker       │
└───────┬──────────────┬──────────────┬─────────┬─────────┘
        │              │              │         │
┌───────▼──────┐ ┌─────▼──────┐ ┌────▼───────┐ │
│ Job Scraper  │ │  Resume    │ │ Application│ │
│              │ │  Pipeline  │ │ Materials  │ │
│ 9 scrapers   │ │ Parse/Match│ │ Cover Ltrs │ │
│ JobSpy lib   │ │ Tailor/Val │ │ Draft Q&A  │ │
└───────┬──────┘ └──────┬─────┘ └────────────┘ │
        │               │                      │
┌───────▼──────┐ ┌──────▼─────┐ ┌──────────────▼─┐
│   Source     │ │ PDF Engine │ │  Application   │
│   Registry   │ │ Chrome +   │ │  Autofill      │
│   14 sources │ │ Fallback   │ │  Selenium ATS  │
└──────────────┘ └────────────┘ └────────────────┘
```

## Active Sources (8 enabled)

| Platform | Method | Auth | Data Quality |
|----------|--------|------|-------------|
| **Remotive** | Public API | None | Salary, tags, descriptions |
| **We Work Remotely** | HTML parsing | None | Titles, companies, regions |
| **Remote OK** | Public API | None | Salary ranges, tags |
| **LinkedIn** | JobSpy library | None | Full listings via scraping |
| **Indeed** | JobSpy library | None | Full listings via scraping |
| **Glassdoor** | JobSpy library | None | Full listings via scraping |
| **Himalayas** | Free JSON API | None | Salary, seniority, timezones |
| **Jobicy** | Free JSON API | None | Salary ranges, job levels |

> **Adzuna** is also supported but requires `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` environment variables (free signup).

## Features

### Multi-Platform Scraping
- 9 job board integrations with deduplication
- Configurable source registry with compliance metadata
- Per-source timeout enforcement via multiprocessing
- LinkedIn/Indeed/Glassdoor via `python-jobspy` (no API keys needed)

### Intelligent Matching
- Keyword extraction with noise filtering and alias normalization
- Role-family detection (DevOps, Backend, Full Stack, etc.)
- Experience-weighted matching with adjacent skill evidence tracking

### Resume Tailoring
- Multi-format resume parsing (txt, md, doc, docx, rtf, odt, pdf)
- Role-specific headline and summary generation
- Keyword-optimized experience and skill selection with backfill
- Multi-attempt validation loop (up to 5 iterations for best fit)

### Application Packets
- Context-aware cover letter generation
- Draft interview answers (5 standard questions)
- Autofill payload with field mapping for ATS forms
- Combined validation scoring (resume + packet)

### Application Automation
- Selenium-based form autofill for job applications
- ATS provider detection (Greenhouse, Lever, Workday, Ashby, Workable, BambooHR)
- Smart field matching via name, id, placeholder, aria-label attributes
- Resume upload support

### Application Tracking
- Full lifecycle status tracking: `prepared` > `ready_to_review` > `applied` > `interview` > `offer` / `rejected` / `archived`
- Per-job status persistence with notes and timestamps

### Modern Dashboard
- Glassmorphism UI with sidebar navigation
- Dark/light theme with system preference detection
- Advanced filters: salary, experience, date, job type, skills
- Toast notifications, skeleton loading, animated counters
- Responsive design with mobile hamburger menu

### Advanced Filtering
- Salary range parsing (`$30k-$50k`, `$90/hr`, `EUR30k`)
- Experience level inference (junior/mid/senior/lead)
- Date posted cutoffs (today, 3 days, week, month)
- Job type, skills, and source filtering

## Quick Start

### Prerequisites
- Python 3.11+
- Google Chrome (for PDF generation and autofill, optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/rishat5081/job-scrapper.git
cd job-scrapper

# One-command bootstrap (installs system packages + Python deps + starts server)
./start.sh

# Or manual setup:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run

```bash
# Bootstrap dependencies and start the server
./start.sh

# Or, if dependencies are already installed:
./scripts/start_server.sh

# Or manually:
PYTHONPATH=src python -m jobintel.api_server

# Open the dashboard
open http://localhost:8080
```

### Daily Task Run

```bash
# Scrape today's batch, rank relevant engineering jobs, generate tailored PDFs,
# and write JSON + Markdown reports under data/reports/
PYTHONPATH=src python scripts/run_today_tasks.py \
  --allow-scraped-today-fallback \
  --min-match-score 90 \
  --min-validation-score 70
```

### Optional: Adzuna Integration

```bash
export ADZUNA_APP_ID="your_app_id"
export ADZUNA_APP_KEY="your_app_key"
```

## API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/sources` | List all source definitions + last scrape report |
| `GET` | `/api/stats` | Dashboard statistics (includes prepared application count) |
| `POST` | `/api/scrape` | Trigger job scraping from all enabled sources |
| `GET` | `/api/scraped-jobs` | List jobs with filters and pagination |
| `GET` | `/api/filter-options` | Available filter values (tags, types, sources) |

### Resume & Tailoring Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/profile` | Get current resume profile |
| `POST` | `/api/profile/upload` | Upload and parse a resume file |
| `GET` | `/api/matches` | Get jobs ranked by profile match |
| `POST` | `/api/jobs/:id/tailor` | Generate tailored resume + application packet |
| `POST` | `/api/jobs/:id/prepare-application` | Alias for tailor (full packet) |
| `POST` | `/api/pipeline/run` | Batch generate resumes for top matches |
| `POST` | `/api/pipeline/refresh` | Scrape + match + generate in one pass |
| `GET` | `/api/generated-resumes` | List all generated resume artifacts |
| `GET` | `/api/generated-resumes/:filename` | Download a generated PDF |
| `GET` | `/api/generated-files/:filename` | Download cover letters, draft answers, etc. |

### Application Lifecycle Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/jobs/:id/status` | Get application status for a job |
| `POST` | `/api/jobs/:id/status` | Update application status and notes |
| `POST` | `/api/jobs/:id/autofill` | Launch Selenium autofill session |
| `GET` | `/api/application-tracker` | Full application tracker across all jobs |

### Filter Parameters (`/api/scraped-jobs`)

| Parameter | Type | Example |
|-----------|------|---------|
| `search` | string | `python backend` |
| `location` | string | `remote` |
| `remote_policy` | string | `remote`, `onsite`, `hybrid` |
| `source_key` | string | `linkedin`, `remotive` |
| `salary_min` | int | `50000` |
| `salary_max` | int | `150000` |
| `experience_level` | string | `junior`, `mid`, `senior`, `lead` |
| `date_posted` | string | `today`, `3days`, `week`, `month` |
| `job_type` | string | `Full-time`, `Contract` |
| `skills` | string | `react,python,aws` (comma-separated) |
| `page` | int | `1` |
| `per_page` | int | `12` |

## Project Structure

```
jobs/
├── src/
│   └── jobintel/                  # Main Python package
│       ├── __init__.py            # Package init, PROJECT_ROOT, DATA_DIR, TEMPLATES_DIR
│       ├── api_server.py          # Flask API server (25+ endpoints)
│       ├── job_scraper.py         # Multi-platform scraper + filters + timeouts
│       ├── source_registry.py     # Source definitions + compliance metadata
│       ├── resume_pipeline.py     # Resume parsing, matching, tailoring, validation
│       ├── pdf_utils.py           # PDF generation (Chrome headless + fallback)
│       ├── application_materials.py  # Cover letters, draft answers, packet validation, status tracking
│       ├── application_autofill.py   # Selenium ATS form autofill + provider detection
│       └── job_monitor.py         # macOS job monitoring + notifications
├── templates/
│   ├── live_dashboard.html        # Modern glassmorphism dashboard UI
│   ├── dashboard.html             # Alternate dashboard
│   └── automation_harness.html    # Browser automation test harness
├── scripts/
│   ├── run_today_tasks.py         # Daily scrape/match/tailor/validate report runner
│   ├── start_server.sh            # Start Flask dev server
│   ├── auto_scraper.sh            # Automated periodic scraping
│   ├── check_jobs.sh              # macOS notification reminder
│   ├── install.sh                 # One-command setup
│   ├── setup_alerts.sh            # macOS launchd alert setup
│   ├── setup_auto_scraper.sh      # macOS launchd scraper setup
│   └── browser_automation_run.mjs # Chrome DevTools browser automation
├── tests/
│   ├── test_api_server.py         # Flask endpoint tests
│   ├── test_job_scraper.py        # Scraper + filter + timeout tests
│   ├── test_resume_pipeline.py    # Resume pipeline + PDF + validation tests
│   ├── test_source_registry.py    # Source registry tests
│   └── test_application_autofill.py  # Autofill detection + field matching tests
├── docs/
│   ├── START_HERE.md              # Quick start guide
│   ├── QUICK_REFERENCE.md         # Command cheat sheet
│   ├── SETUP_GUIDE.md             # Installation + configuration
│   ├── README_SCRAPER.md          # Scraping behavior + daily workflow
│   └── SYSTEM_OVERVIEW.md         # Architecture + component map
├── data/                          # Runtime data (gitignored)
│   ├── uploads/
│   ├── generated_resumes/
│   └── reports/
├── .github/workflows/
│   ├── ci.yml                     # Test suite + coverage
│   ├── lint.yml                   # Ruff + HTML + JS validation
│   ├── security.yml               # Dependency audit + Bandit + secrets
│   ├── codeql.yml                 # GitHub CodeQL analysis
│   ├── dependency-review.yml      # PR dependency review
│   ├── release.yml                # Changelog on tag push
│   └── stale.yml                  # Stale issue/PR management
├── start.sh                       # Cross-platform bootstrap (macOS/Linux/Windows)
├── pyproject.toml                 # Project metadata + tool config
├── requirements.txt               # Python dependencies
├── .editorconfig                  # Editor settings
├── .gitignore
├── LICENSE
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
└── SECURITY.md
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=jobintel --cov-report=term-missing

# Run specific test file
python -m pytest tests/test_job_scraper.py -v
```

## Code Quality

```bash
# Lint with Ruff
ruff check src/ tests/

# Format with Ruff
ruff format src/ tests/

# Security scan with Bandit
bandit -r src/ -x ./venv,./tests

# Type checking (optional)
mypy src/jobintel/ --ignore-missing-imports
```

## CI/CD Pipelines

This project includes production-grade GitHub Actions workflows:

| Workflow | Trigger | What it does |
|----------|---------|-------------|
| **CI** | Push/PR to main | Runs test suite on Python 3.11/3.12, reports coverage |
| **Lint** | Push/PR to main | Ruff linting + formatting check, HTML validation |
| **Security** | Push/PR + weekly schedule | `pip-audit` dependency scan, Bandit SAST |
| **CodeQL** | Push/PR + weekly schedule | GitHub CodeQL semantic analysis for Python |
| **Dependency Review** | Pull requests | Checks new dependencies for vulnerabilities |
| **Release** | Tag push (`v*`) | Auto-generates changelog from commits |
| **Stale** | Daily schedule | Marks and closes stale issues/PRs |

## Validation Rules

The tailoring engine does **not** invent unsupported claims. If a job description asks for skills not evidenced in the uploaded resume, the validator flags them as `unsupported` instead of fabricating them. Each generated artifact includes:

- **Match score**: Profile-to-job keyword overlap (0-100)
- **Validation score**: Coverage of evidenced keywords in the output (resume + packet combined)
- **Fit label**: `strong_alignment`, `partial_alignment`, or `insufficient_evidence`
- **Adjacent keywords**: Skills inferred from related evidence (e.g., TypeScript from JavaScript)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## Security

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.
