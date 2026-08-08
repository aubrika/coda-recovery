#!/usr/bin/env bash
# Fetch the phase-2 datasets (not committed — no explicit license; these are the
# public data-availability deposits for the respective papers, for research use).
set -euo pipefail
cd "$(dirname "$0")/raw"
# Hersh et al. 2022 (PNAS) — 7 Pacific clans, OSF ae6pd. THE second-system source.
curl -sL "https://osf.io/download/9hwmj/" -o hersh2022_pacific_coda.csv
# Sharma et al. 2024 (Nat Commun) — Dominica EC1, richer than Gero (individual IDs).
curl -sL "https://raw.githubusercontent.com/pratyushasharma/sw-combinatoriality/main/data/DominicaCodas.csv" -o sharma2024_dominica_coda.csv
echo "fetched. expected sha256:"
echo "  hersh:  96bbf264286eadc94c3d2d68229b133fa135733f759c0bad915c66ccd7a84acf"
echo "  sharma: 53dd44fbfb0040da93656aa44883954f3abe18dd6539e90c625af86a96db6b45"
