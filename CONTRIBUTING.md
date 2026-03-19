# Contributing to JobIntel

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

```bash
# Clone and set up
git clone https://github.com/rishat5081/job-scrapper.git
cd job-scrapper
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

```bash
# Lint
ruff check .

# Format
ruff format .

# Run tests
python -m pytest tests/ -v
```

### Before Submitting

1. All tests pass: `python -m pytest tests/ -v`
2. No lint errors: `ruff check .`
3. Code is formatted: `ruff format --check .`
4. No security issues: `bandit -r . -x ./venv,./tests -ll`

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes with tests
4. Ensure all CI checks pass
5. Submit a pull request with a clear description

## Adding a New Job Source

1. Add a `SourceDefinition` entry in `source_registry.py`
2. Create a scraper function in `job_scraper.py`
3. Register it in the `SCRAPERS` dict
4. Add tests in `tests/test_job_scraper.py`
5. Update the README source table

## Reporting Issues

- Use GitHub Issues with a clear title and description
- Include steps to reproduce for bugs
- Tag with appropriate labels (bug, enhancement, etc.)
