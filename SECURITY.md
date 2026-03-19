# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

1. **Do not** open a public GitHub issue for security vulnerabilities
2. Email the maintainer directly with details
3. Include steps to reproduce the vulnerability
4. Allow reasonable time for a fix before public disclosure

## Security Measures

This project implements the following security practices:

- **Dependency auditing**: Automated `pip-audit` scans on every push and weekly
- **SAST scanning**: Bandit static analysis for Python security issues
- **CodeQL analysis**: GitHub CodeQL for semantic vulnerability detection
- **Secret detection**: Automated scanning for accidentally committed secrets
- **License compliance**: Automated checks for copyleft license dependencies
- **Dependency review**: GitHub dependency review on all pull requests

## Data Handling

- Resume data is stored locally and never transmitted to external services
- Job scraping uses only publicly available APIs and data
- No personal data is collected beyond what the user explicitly uploads
- All API keys (e.g., Adzuna) are loaded from environment variables, never hardcoded
