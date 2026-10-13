# Figures

Every figure here is written by code in this repository from the fetched inputs.
None is edited by hand.

| Figure | Written by | Reads | Shows |
|---|---|---|---|
| `1_the_data_model.png` | `plain_figures` | fetched data | Coda counts by rhythm template and fixed duration bin, all eight clans pooled (23,684 codas) |
| `2_current_predicts_next.png` | `plain_figures` | `results/predictive_info_sweep.csv` | Changes-only gains for tempo and rhythm in each clan, with 95% recording-bootstrap intervals |
| `3_shared_vs_clan_specific.png` | `universal_structure` | fetched data | Changes-only gain of each clan's own model against a model fitted on the other seven |
| `4_cross_prediction.png` | `clan_similarity` | fetched data | Pairwise cross-prediction: clan A's bigram scored on clan B, all pairs including repeats |
| `5_procrustes_distance.png` | `clan_similarity` | fetched data | Procrustes distance between clans' transition embeddings |
| `6_distance_vs_predictability.png` | `drift` | fetched data | Figures 4 and 5 compared pair by pair, with exact Mantel tests |
| `7_ordering_tempo.png` | `ordering_drift` | fetched data | Tempo, changes only, shared duration bins: Procrustes distance against ordering lost |
| `8_ordering_rhythm.png` | `ordering_drift` | fetched data | The same for the shared rhythm classes, where clans' own gains are near zero |

Figure 2 needs `predictive_info_sweep` to have run first. The numbers behind figures
3 to 8 are saved alongside them in `results/` by the same scripts.

## Checking them

Run the commands in the [README](../../README.md#reproduce). All random steps are
seeded, so the result CSVs come out byte-identical and the figures pixel-identical
to the committed ones. Last checked on 2026-10-12 with Python 3.14.4 and the pinned
versions in `requirements.txt`. PNG files can still differ in their bytes, because
matplotlib writes its version into the file metadata.

## Reading notes

- Figures 4 and 5 show cross-prediction scores and embedding distances. Neither
  establishes a grammar.
- Figure 5's colour scale spans the observed distances (0.72 to 1.05), not zero
  upward, and leaves the diagonal blank.
- Figures 1, 3, 4 and 5 use fixed duration bins shared across clans. Figure 2 uses
  per-clan quantile bins, so its tempo scores are not comparable with theirs.
