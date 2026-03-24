# Contributing to JobIntel

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

```bash
# Clone and set up
git clone https://github.com/rishat5081/job-scrapper.git
cd job-scrapper

# One-command bootstrap
./start.sh --install-only

# Or manual setup:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install ruff pytest pytest-cov bandit
```

## Code Quality Standards

### Python
- **Linter**: Ruff (configured in `pyproject.toml`)
- **Style**: PEP 8 with 120 char line length
- **Type hints**: Encouraged for public functions
- **Imports**: Always use `jobintel.` prefix for cross-module imports

```bash
# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=jobintel --cov-report=term-missing
```

### Before Submitting

1. All tests pass: `python -m pytest tests/ -v`
2. No lint errors: `ruff check src/ tests/`
3. Code is formatted: `ruff format --check src/ tests/`
4. No security issues: `bandit -r src/ -x ./venv,./tests -ll`

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes with tests
4. Ensure all CI checks pass
5. Submit a pull request with a clear description

## Adding a New Job Source

1. Add a `SourceDefinition` entry in `src/jobintel/source_registry.py`
2. Create a scraper function in `src/jobintel/job_scraper.py`
3. Register it in the `SCRAPERS` dict
4. Add tests in `tests/test_job_scraper.py`
5. Update the README source table

## Adding a New ATS Provider

1. Add the URL pattern to `detect_application_provider()` in `src/jobintel/application_autofill.py`
2. Add field hint patterns if the provider uses non-standard form field naming
3. Add tests in `tests/test_application_autofill.py`

## Reporting Issues

- Use GitHub Issues with a clear title and description
- Include steps to reproduce for bugs
- Tag with appropriate labels (bug, enhancement, etc.)
