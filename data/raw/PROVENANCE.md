# Data provenance

Two sperm-whale sources, fetched separately from the repository. The input bytes
used for the September 2026 rerun are pinned by SHA-256 in
[`../sources.json`](../sources.json). Run `python data/fetch.py all --verify`
from the repository root to check local inputs. The fetcher also checks downloaded
bytes before writing them. These digests record the existing analysis inputs;
they are not an independent audit of the deposits.

EC1 preprocessing and rhythm-template loading read Python pickles. The native
EC1 rows are cached as CSV after preprocessing; template loading still reads
`mean_codas.p`. The previous claim that the pipeline never unpickles was incorrect.

## hersh2022_pacific_coda.csv — the 7 Pacific clans (fetch via ../fetch_phase2.sh)
- Hersh et al. 2022, PNAS 119:e2201692119. OSF osf.io/ae6pd, file 9hwmj.
- 24,237 codas (97% typed), **7 Pacific clans** (REG/SH/FP/PALI/PO/RI/SI), none is
  the Caribbean EC1. `coda_type` is a GLOBAL scheme (94/100 types shared by ≥2 clans).
- Fields: coda_type, grpvar (repertoire = session), coda_number (order), clan_name,
  nclicks, duration, ICI1..28. No individual ID (repertoire-level only).
- sha256 96bbf264286eadc94c3d2d68229b133fa135733f759c0bad915c66ccd7a84acf
- Licence: OSF node_license = null. Research/reproduction use.

## sharma/ — Sharma 2024 factored model, EC1 (fetch via ../fetch_sharma.sh)
- Sharma et al. 2024, Nat Commun 15:3617; github pratyushasharma/sw-combinatoriality
  (Zenodo 10.5281/zenodo.10817697). Paper is CC BY 4.0; repo has NO LICENSE file,
  so raw + de-pickled data are gitignored (fetch + rebuild locally).
- Dataset 2 = `sperm-whale-dialogues.csv`: 3840 DTag codas, ordered, REC (deployment),
  Whale (speaker), TsTo (absolute onset s), raw ICIs. After >10-click exclusion: 3687.
- rhythm (0..17) from `rhythms.p`, ornament from `ornaments.p` (per-coda, row-aligned;
  verified 100% vs nearest `mean_codas.p` template). tempo (0..4) from Duration bins
  reproducing `tempos-dict.p` clusters; rubato_dir derived per paper (Section 3).
- Native EC1 rows are converted to a local CSV by `coda_model.py`.
  Audited field-level inventory in `../inventory/factored_inventory.md`.
