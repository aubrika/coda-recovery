# Data provenance

## gero2016_coda_ici.xlsx
- Source: Dryad, doi:10.5061/dryad.ck4h0 (Gero, Whitehead & Rendell 2016,
  "Individual, unit, and vocal clan level identity cues in sperm whale codas",
  R. Soc. Open Sci.). File 28886, 353,910 bytes.
- Retrieved 2026-08-06 via browser (Dryad now fronts downloads with an Anubis
  proof-of-work gateway; the public API file endpoint returns 401 without a
  bearer token). sha256 recorded alongside the file.
- Licence: Dryad deposits are released under CC0.
- Single sheet "Gero et al ICIdata", 4116 rows. See ../inventory/ for the
  audited field-level inventory.

## NOT USED
- HuggingFace `orrp/DSWP`: 1503 raw .wav files only (WhAM pipeline audio input),
  no type labels / ordering / speaker attribution. Not usable for this analysis.

## PHASE 2 (fetch via ../fetch_phase2.sh — gitignored, no explicit license)

### hersh2022_pacific_coda.csv  — THE second system
- Hersh et al. 2022, PNAS 119:e2201692119. OSF osf.io/ae6pd, file 9hwmj.
- 24,237 codas (97% typed), **7 Pacific clans** (REG/SH/FP/PALI/PO/RI/SI), none is
  Gero/Sharma's Caribbean EC1. coda_type is a GLOBAL scheme (94/100 types shared
  by >=2 clans) -> cross-clan alignment has a checkable answer key.
- Fields: coda_type (label), grpvar (repertoire = session), coda_number (order),
  clan_name. NO individual ID (repertoire-level only). sha256 96bbf264286eadc94c3d2d68229b133fa135733f759c0bad915c66ccd7a84acf
- License: OSF node_license = null. Research/reproduction use.

### sharma2024_dominica_coda.csv — richer EC1 (same clan as Gero, an upgrade)
- Sharma et al. 2024, Nat Commun 15:3617. github pratyushasharma/sw-combinatoriality
  data/DominicaCodas.csv; Zenodo 10.5281/zenodo.10817697.
- 8,718 codas, Clan uniformly EC1. Adds IDN (individual) + UnitNum vs Gero.
- Not a second system; a curated/larger version of the primary clan. sha256 53dd44fbfb0040da93656aa44883954f3abe18dd6539e90c625af86a96db6b45
- License: GitHub repo license = null (all-rights-reserved despite public posting).
