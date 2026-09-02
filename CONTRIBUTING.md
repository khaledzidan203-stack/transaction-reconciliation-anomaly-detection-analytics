# Contributing

Thank you for your interest in contributing to this project.

## Privacy First

This project uses **only synthetic data**. No real business data, personal information, company identifiers, or proprietary content may be added.

Before submitting any contribution, verify:

- [ ] No real names, identifiers, or codes
- [ ] No real company or system names
- [ ] No real financial or transaction data
- [ ] No credentials, API keys, or secrets
- [ ] No local file paths or environment-specific values
- [ ] All sample data is reproducible with a fixed seed

## How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Write or update tests for any new logic
4. Ensure all tests pass (`pytest tests/ -v`)
5. Run the privacy checklist (`PRIVACY_CHECKLIST.md`)
6. Commit with a clear, descriptive message
7. Push to your fork and open a pull request

## Code Style

- Python: follow PEP 8
- SQL: use uppercase keywords, lowercase identifiers
- Markdown: one sentence per line in documentation
- Keep functions small and single-purpose
- Document all public functions with docstrings

## Testing

All contributions must include tests. Run:

```bash
pytest tests/ -v
```

## Reporting Issues

Use GitHub Issues to report bugs or suggest improvements. Include:

- Description of the issue
- Steps to reproduce (if applicable)
- Expected vs actual behavior
- Environment details

Thank you for helping improve this project.
