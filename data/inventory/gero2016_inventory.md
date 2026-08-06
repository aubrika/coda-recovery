# EC-1 coda deposit — M1 inventory

Source: `data/raw/gero2016_coda_ici.xlsx`  ·  rows: **4116**

## Required-field verdict (spec Section 4)

- **timestamp** — **MISSING / substituted**: NO sub-second timestamp. Only day-level 'Date' (Excel serial) spanning 2005-01-15..2010-04-17 over 78 distinct days. Ordering is instead carried by 'CodaNumber', a globally-unique, monotonic recording index. => seconds-based inter-coda gap (spec 5.1) is NOT computable; substitute a CodaNumber-gap (see session_key_codanumber_gaps).

- **coda_type_label** — PRESENT: 'CodaName': 21 real coda types after dropping ['NOISE'] (240 NOISE rows). Matches the ~21-22 EC-1 types the spec expects.

- **speaker_id** — PRESENT: 'WhaleID': 18 distinct values INCLUDING the 0 sentinel. Only 1602 of 3876 codas (41.3%) are speaker-attributed; the rest are WhaleID==0 (unattributed). This is the binding constraint: the within/between-speaker split (spec 5.1) and the by-individual ladder rung (6.4) can only use the attributed subset.


## Coda types

21 types: 1+1+3, 1+31, 1+32, 10I, 2+3, 3D, 3R, 4D, 4R1, 4R2, 5R1, 5R2, 5R3, 6D, 6I, 7D, 7I, 8D, 8I, 9D, 9I


Counts (desc):

- 1+1+3: 1512
- 5R1: 1007
- 4D: 217
- 7D: 152
- 5R2: 133
- 8I: 124
- 7I: 114
- 9I: 91
- 6D: 76
- 1+31: 70
- 4R1: 65
- 4R2: 60
- 1+32: 56
- 2+3: 49
- 10I: 33
- 8D: 30
- 6I: 23
- 3D: 23
- 3R: 17
- 9D: 13
- 5R3: 11

## Speakers / units

- real speakers: 17  ·  attributed: 41.3%
- units: 9 [1, 2, 3, 4, 5, 6, 7, 8, 9]
- days: 78  span 2005-01-15..2010-04-17
- CodaNumber: 1..4325, unique=True, missing-in-range=209

## Power projection — transitions per cell (split-half)

The number that predicts whether anything works. n^2 cells; a split-half roughly halves the pairs available to each matrix.

- **by_date_gap1**: n=21, cells=441; pairs all=3626 (→ 4.111/cell), pairs both-attributed=1462 (→ 1.658/cell)
- **by_date_unit_gap1**: n=21, cells=441; pairs all=3626 (→ 4.111/cell), pairs both-attributed=1462 (→ 1.658/cell)
- **by_date_gap3**: n=21, cells=441; pairs all=3752 (→ 4.254/cell), pairs both-attributed=1508 (→ 1.71/cell)
