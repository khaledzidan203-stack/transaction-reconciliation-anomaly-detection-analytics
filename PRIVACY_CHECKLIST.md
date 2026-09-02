# Privacy Checklist

Use this checklist before every major commit to ensure no real or sensitive data enters the repository.

## Pre-Commit Scan

### Personal Data
- [ ] No real employee names
- [ ] No real customer / patient names
- [ ] No real pharmacist names
- [ ] No real phone numbers
- [ ] No real email addresses
- [ ] No real National IDs / Iqama / passport numbers
- [ ] No real usernames or account identifiers
- [ ] No real personal file paths

### Company / Confidential Data
- [ ] No real company names
- [ ] No real branch identifiers
- [ ] No real employee codes
- [ ] No real internal system names
- [ ] No real proprietary workflow names
- [ ] No real internal report terminology
- [ ] No real confidential business rules
- [ ] No real source Excel files
- [ ] No real exported business reports
- [ ] No real company logos or branding

### Transaction / Financial Data
- [ ] No real transaction IDs
- [ ] No real prescription numbers
- [ ] No real invoice numbers
- [ ] No real authorization numbers
- [ ] No real pharmacy license numbers
- [ ] No real product datasets
- [ ] No real sales / pricing / financial data
- [ ] No real transaction amounts

### Credentials / Secrets
- [ ] No API keys
- [ ] No passwords
- [ ] No tokens
- [ ] No connection strings
- [ ] No server addresses
- [ ] No database credentials
- [ ] No private keys (.pem, .key, .p12, .pfx)
- [ ] No certificates (.crt, .cer)

### Technical
- [ ] No local Windows paths (C:\, D:\, etc.)
- [ ] No environment-specific configuration
- [ ] No .env files with real values
- [ ] No credentials files
- [ ] No screenshots containing real data

## Synthetic Data Verification

- [ ] All data is generated with a fixed random seed
- [ ] All names are fictional
- [ ] All identifiers are fictional
- [ ] All amounts are fictional
- [ ] All dates are fictional or generic
- [ ] Data is fully reproducible

## Git History Verification

- [ ] No sensitive data in any previous commit
- [ ] No sensitive data in git notes
- [ ] No sensitive data in deleted files
- [ ] No sensitive data in branch history

## Final Publication Gate

| Criterion | Target | Status |
|---|---|---|
| Personal data findings | 0 | ☐ |
| Company confidential data findings | 0 | ☐ |
| Credentials / secrets | 0 | ☐ |
| Real datasets | 0 | ☐ |
| Real transaction identifiers | 0 | ☐ |
| Private local paths | 0 | ☐ |
| Sensitive Git history | 0 | ☐ |

**All criteria must be 0 before publishing to GitHub.**

## How to Scan

### Manual Scan
- Review all new files before committing
- Search for known real identifiers
- Check file names and directory names
- Review commit messages

### Automated Scan (Future)
- Implement pre-commit hooks to scan for patterns
- Use tools like `git-secrets` or `trufflehog`
- Add CI checks for sensitive patterns

## If Sensitive Data Is Found

1. **Do not commit** the file
2. Remove or replace the sensitive content
3. If already committed, use `git filter-branch` or BFG Repo Cleaner to remove from history
4. Rotate any exposed credentials immediately
5. Update this checklist to prevent recurrence

## Contact

If unsure whether content is safe to commit, consult the repository maintainer before proceeding.
