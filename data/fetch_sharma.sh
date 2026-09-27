#!/usr/bin/env bash
# Compatibility wrapper; the Python fetcher verifies source digests.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python "$ROOT/data/fetch.py" sharma
cd "$ROOT"
PYTHONPATH=src python -c "from coda_recovery.coda_model import build_from_deposit; build_from_deposit()"
