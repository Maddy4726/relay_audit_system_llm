#!/usr/bin/env bash
# Run batch extraction from the repository root.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -z "${OPENAI_API_KEY:-}" ]] && [[ ! -f relay_audit_system/.env ]]; then
  echo "ERROR: Set OPENAI_API_KEY or create relay_audit_system/.env"
  echo "  cp relay_audit_system/.env.example relay_audit_system/.env"
  exit 2
fi

pip install -q -r relay_audit_system/requirements.txt
export PYTHONPATH="$ROOT"
python3 -m relay_audit_system.main "$@"
