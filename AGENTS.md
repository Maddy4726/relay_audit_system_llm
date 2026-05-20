# Relay Audit System — Agent Guide

## Cursor Cloud specific instructions

### Overview

Single Python CLI application that extracts structured data from industrial relay feeder test reports (DOCX) into canonical JSON using the OpenAI Responses API. No web server, no database, no Docker.

### Running the application

```bash
PYTHONPATH=. python -m relay_audit_system.main          # batch extraction
PYTHONPATH=. python -m relay_audit_system.main --help   # CLI options
PYTHONPATH=. python -m relay_audit_system.main --file <name>.docx  # single file
```

`PYTHONPATH=.` (from the repo root) is required because there is no `setup.py`/`pyproject.toml`.

### Required secrets

- `OPENAI_API_KEY` — must be set as an environment variable or in `relay_audit_system/.env`. Without it the app exits with code 2.

### Verify API key

```bash
PYTHONPATH=. python -m relay_audit_system.tools.verify_api
```

### Input / output

- Place `.docx` files in `relay_audit_system/input_docs/`.
- JSON output is written to `relay_audit_system/extracted_json/`.

### No tests / lint / build

This repository has no automated tests, no linter configuration, and no build step. The code runs directly as a Python module.
