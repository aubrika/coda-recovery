#!/usr/bin/env bash
# Compatibility wrapper for the Pacific source.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python "$ROOT/data/fetch.py" hersh
