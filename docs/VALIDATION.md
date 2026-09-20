# Validation

The 0.2.0 integration branch includes pytest coverage for task normalization, local-first network detection, and the OBEOS HTTP client boundary.

The ChatGPT execution environment used to prepare this branch could access GitHub through the connected GitHub app but could not resolve `github.com` from a normal shell, so a clean clone/install/test run could not be completed there. Run locally before merge:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
```

Then smoke-test the runtime:

```bash
python -m nightwatch
nightwatch status
```
