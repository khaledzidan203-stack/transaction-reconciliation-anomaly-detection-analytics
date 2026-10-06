# Environment Baseline

## CI environment

GitHub Actions validates the repository using:

- Ubuntu latest
- Python 3.12
- dependencies from `requirements.txt`

Current dependency ranges:

- pandas >= 2.0.0
- NumPy >= 1.24.0
- RapidFuzz >= 3.0.0
- pytest >= 7.0.0

These are compatibility ranges, not a locked environment.

## Reproducibility model

The synthetic generator is deterministic through:

- fixed seed `20260902`;
- repository-relative paths;
- deterministic CSV writing;
- SHA-256 file fingerprints;
- committed `generation_manifest.json`;
- automated regeneration tests.

## Runtime boundaries

- Python engine: executable in CI.
- SQL: analytical scripts only; no database runtime is provisioned in CI.
- HTML dashboard: committed executable browser artifact.
- Power BI: design blueprint only; no Desktop runtime is claimed.
