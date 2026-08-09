#!/usr/bin/env bash
# Fetch the Pacific multi-clan dataset (not committed — no explicit license; this is
# the public data-availability deposit for the paper, for research use).
set -euo pipefail
cd "$(dirname "$0")/raw"
# Hersh et al. 2022 (PNAS) — 7 Pacific clans, OSF ae6pd. THE second-system source.
curl -sL "https://osf.io/download/9hwmj/" -o hersh2022_pacific_coda.csv
echo "fetched. expected sha256:"
echo "  hersh:  96bbf264286eadc94c3d2d68229b133fa135733f759c0bad915c66ccd7a84acf"
