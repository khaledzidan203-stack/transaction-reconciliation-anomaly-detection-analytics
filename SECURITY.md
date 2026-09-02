# Security Policy

## Synthetic Data Only

This project contains **no real data**. All data is synthetic and generated deterministically with a fixed random seed.

## What This Project Does NOT Contain

- Real customer, employee, or patient data
- Real company names or identifiers
- Real transaction records
- Real financial data
- API keys, passwords, or tokens
- Connection strings or server addresses
- Proprietary business logic or workflows

## Reporting Vulnerabilities

If you discover a security vulnerability in the code (e.g., a dependency vulnerability, injection risk, or logic flaw), please report it responsibly:

1. Do **not** open a public issue for security vulnerabilities
2. Contact the repository maintainer directly
3. Allow reasonable time for the issue to be addressed before public disclosure

## Privacy Guarantees

- No data is sent to external services
- No network calls are made during analysis
- All processing is local
- No telemetry or analytics
- No third-party data sharing

## Dependencies

Dependencies are kept minimal. Review `requirements.txt` before installation.

## Git Hygiene

- `.gitignore` blocks data files, credentials, and sensitive directories
- `.gitattributes` enforces consistent line endings
- No secrets are committed
- Commit messages do not contain sensitive information
