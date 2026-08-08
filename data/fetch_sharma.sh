#!/usr/bin/env bash
# Fetch the Sharma et al. 2024 deposit (Dataset 2 + rhythm/tempo/ornament labels)
# and de-pickle into a plain CSV. Not committed (no explicit repo licence; the
# paper is CC BY 4.0 but the GitHub repo carries no LICENSE file).
set -euo pipefail
cd "$(dirname "$0")/raw/sharma" 2>/dev/null || { mkdir -p "$(dirname "$0")/raw/sharma"; cd "$(dirname "$0")/raw/sharma"; }
B="https://raw.githubusercontent.com/pratyushasharma/sw-combinatoriality/main/data"
for f in sperm-whale-dialogues.csv rhythms.p ornaments.p tempos-dict.p mean_codas.p; do
  curl -sL "$B/$f" -o "$f"
done
echo "fetched. de-pickling -> data/derived/ec1_dataset2.csv"
cd "$(dirname "$0")/.."
PYTHONPATH=src python -c "from coda_recovery.coda_model import build_from_deposit; build_from_deposit()"
