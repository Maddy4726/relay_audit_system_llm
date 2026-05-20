# Relay Audit System (LLM Extraction)

Extract industrial relay feeder test reports from DOCX files into canonical JSON.

## Safe API key setup

**Never** commit real API keys to git, chat, or `.env.example`.

### Option A — Cursor secrets (recommended for Cloud Agent)

1. Open **Cursor Settings → Cloud Agent / Environment Variables**
2. Add: `OPENAI_API_KEY` = your key from https://platform.openai.com/api-keys
3. Optional: `OPENAI_MODEL` = `gpt-4.1-mini`

### Option B — Local `.env` file (recommended on your machine)

```bash
cp relay_audit_system/.env.example relay_audit_system/.env
# Edit .env and paste your key on the OPENAI_API_KEY= line
```

Or use the interactive helper (hidden input, does not echo the key):

```bash
pip install -r relay_audit_system/requirements.txt
PYTHONPATH=. python -m relay_audit_system.tools.setup_env
```

### Verify the key works

```bash
PYTHONPATH=. python -m relay_audit_system.tools.verify_api
```

### Run extraction

```bash
./relay_audit_system/run.sh
# or
PYTHONPATH=. python -m relay_audit_system.main
```

## Layout

- `input_docs/` — place `.docx` reports here
- `extracted_json/` — JSON output
- `schemas/` — Pydantic models
- `extraction/` — OpenAI Responses API pipeline
