"""Verify OpenAI API key is configured and valid (does not print the key)."""

from __future__ import annotations

import sys

from openai import OpenAI

from relay_audit_system.utils.config import load_settings
from relay_audit_system.utils.logging_config import setup_logging


def main() -> int:
    setup_logging()
    try:
        settings = load_settings()
    except Exception as exc:
        print(f"Configuration error: {exc}")
        return 2

    key = settings.openai_api_key
    if not key or key.startswith("sk-your"):
        print("No valid API key found. Set OPENAI_API_KEY in relay_audit_system/.env")
        return 2

    print(f"Key loaded ({len(key)} characters), model={settings.openai_model}")
    print("Testing OpenAI API...")

    try:
        client = OpenAI(api_key=key)
        models = client.models.list()
        print(f"API status: OK ({len(models.data)} models available)")
        return 0
    except Exception as exc:
        print(f"API status: FAIL — {type(exc).__name__}")
        err = str(exc)
        if "401" in err:
            print("The key is invalid or revoked. Create a new key at https://platform.openai.com/api-keys")
        else:
            print(err[:200])
        return 1


if __name__ == "__main__":
    sys.exit(main())
