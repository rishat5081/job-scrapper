# AGENTS.md — JobIntel

> Universal context file for AI coding agents (Claude Code, Codex, Cursor, Copilot, etc.).

## Quick Start

```bash
# Bootstrap everything (cross-platform)
./start.sh

# Tests
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

## Project Identity

| Field | Value |
|-------|-------|
| Name | JobIntel |
| Type | Flask web app (job scraping + resume pipeline) |
| Stack | Python 3.11+, Flask, Selenium, Chrome headless |
| Linting | Ruff (sole linter/formatter — no flake8, black, isort) |
| Testing | pytest with `pythonpath = ["src"]` in pyproject.toml |
| CI/CD | 7 GitHub Actions workflows |
| Storage | JSON flat files (`data/`) |
| Config | pyproject.toml (ruff, pytest, coverage, mypy, bandit) |

## Architecture

```
src/jobintel/
├── api_server.py          → Flask REST API (22 routes)
├── job_scraper.py         → Multi-platform scraping + filters + timeouts
├── source_registry.py     → Source definitions + compliance metadata
├── resume_pipeline.py     → Resume parsing, matching, tailoring, validation
├── pdf_utils.py           → PDF generation (Chrome headless + fallback)
├── application_materials.py → Cover letters, draft answers, packet validation
├── application_autofill.py  → Selenium ATS form autofill + provider detection
└── job_monitor.py         → macOS job monitoring + notifications
```

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
                   Resume Pipeline → data/generated_resumes/ (PDFs, cover letters)
                                  → data/tailored_resumes.json (artifact registry)
                                  → data/application_tracker.json (status tracking)
                                  → data/reports/ (daily JSON + Markdown reports)
```

## Key Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Live dashboard HTML |
| GET | `/automation-harness` | Automation testing UI |
| GET | `/api/health` | Health check |
| GET | `/api/sources` | List source definitions |
| GET | `/api/profile` | Current resume profile |
| POST | `/api/profile/upload` | Upload + parse resume |
| GET | `/api/filter-options` | Available filter values |
| GET | `/api/scraped-jobs` | Paginated job list (search, filter) |
| POST | `/api/scrape` | Trigger all enabled scrapers |
| GET | `/api/matches` | Jobs ranked by profile match |
| POST | `/api/jobs/:id/tailor` | Generate tailored resume + packet |
| POST | `/api/jobs/:id/prepare-application` | Prepare application packet |
| GET/POST | `/api/jobs/:id/status` | Application status tracking |
| POST | `/api/jobs/:id/autofill` | Launch Selenium form autofill |
| POST | `/api/pipeline/run` | Run full pipeline |
| POST | `/api/pipeline/refresh` | Refresh pipeline data |
| GET | `/api/generated-resumes` | List generated artifacts |
| GET | `/api/generated-resumes/:fn` | Download generated resume |
| GET | `/api/generated-files/:fn` | Download generated file |
| GET | `/api/application-tracker` | Full tracker across all jobs |
| GET | `/api/stats` | Dashboard statistics |

## Key Invariants

1. All cross-module imports use `jobintel.` prefix
2. Path constants defined in `src/jobintel/__init__.py`
3. `patch()` targets use full module paths: `"jobintel.api_server.load_resume_profile"`
4. Ruff is the sole linter/formatter
5. No type stubs required (`ignore_missing_imports = true`)
6. Noise keywords filtered from job keyword extraction
7. Keyword aliases normalize variants (`nodejs` → `node.js`, `ts` → `typescript`)

## Data Files

| File | Purpose |
|------|---------|
| `scraped_jobs.json` | Merged job database |
| `last_scrape.json` | Latest scrape report with source statuses |
| `data/resume_profile.json` | Parsed resume profile |
| `data/tailored_resumes.json` | Artifact registry (resumes + packets) |
| `data/application_tracker.json` | Application status tracking |
| `data/generated_resumes/` | PDFs, cover letters, draft answers |
| `data/reports/` | Daily pipeline reports |

## Specialized Agents

This project includes 15 specialized AI agent definitions in `.claude/agents/`. Each agent has deep project-specific context for the job scraping and resume pipeline.

| Agent | Path | Purpose |
|-------|------|---------|
| project-owner | `.claude/agents/project-owner/` | Audits and updates all agents when the project changes |
| coder | `.claude/agents/coder/` | Feature development across scraper, pipeline, API |
| security-auditor | `.claude/agents/security-auditor/` | PII protection, scraping compliance, Selenium |
| performance | `.claude/agents/performance/` | Scraping speed, API response times, PDF gen |
| standards-enforcer | `.claude/agents/standards-enforcer/` | Ruff, import conventions, naming |
| reviewer | `.claude/agents/reviewer/` | Scraper reliability, API contracts, data integrity |
| tester | `.claude/agents/tester/` | pytest, mock HTTP, coverage targets |
| architect | `.claude/agents/architect/` | Module boundaries, scaling, Flask blueprints |
| devops | `.claude/agents/devops/` | 7 CI workflows, deployment, security scans |
| code-analyzer | `.claude/agents/code-analyzer/` | Complexity, duplication, dependency analysis |
| planner | `.claude/agents/planner/` | Task decomposition, module dependency order |
| production-validator | `.claude/agents/production-validator/` | No TODOs/debug, scraper readiness |
| release-manager | `.claude/agents/release-manager/` | Semver, changelog, security advisories |
| issue-tracker | `.claude/agents/issue-tracker/` | Scraper bug triage, area labels |
| api-docs | `.claude/agents/api-docs/` | API documentation for all 22 endpoints |

### Agent Usage

Each agent is defined as a Markdown file at `.claude/agents/<name>/<name>.md`. They are used by the Claude-Flow orchestration system defined in `claude-flow.config.json`.

**Task routing** automatically assigns work to agents based on patterns:
- Bug fixes → `coder` (primary) + `tester` (verification)
- New features → `architect` (design) → `coder` (implement) → `tester` (test) → `reviewer` (review)
- Security/PII/compliance → `security-auditor`
- Performance/scraping speed → `performance`
- API documentation → `api-docs`
- Releases → `release-manager` + `production-validator`
- CI/CD → `devops`
- Scraper issues → `issue-tracker` (triage) → `coder` (fix)
