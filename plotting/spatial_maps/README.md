# Spatial expression maps

[`build_cscc_spatial_expression_overviews.py`](build_cscc_spatial_expression_overviews.py)
builds cSCC and auxiliary HER2+ maps from saved predictions and per-section
metrics. It also requires plotting helpers from the analysis archive.

[`build_hest_stimage_spatial_expression_overviews.py`](build_hest_stimage_spatial_expression_overviews.py)
builds maps for the HEST and STImage 50-gene benchmarks using a deterministic
representative held-out sample for each organ or tissue group.

Run from the repository root after preparing the required inputs and
configuring the paths in the main [README](../../README.md):

```bash
python plotting/spatial_maps/build_cscc_spatial_expression_overviews.py \
  --output "$MORAP_RESULTS_ROOT/figures/spatial_maps" --dpi 220 --workers 4

python plotting/spatial_maps/build_hest_stimage_spatial_expression_overviews.py \
  --output "$MORAP_RESULTS_ROOT/figures/spatial_maps" --dpi 220
```

The builders check prediction alignment and compare rendered-gene scores
with the corresponding stored metrics. Genes are selected using observed
prediction performance; these panels illustrate individual examples and
should not be used to estimate aggregate predictive performance. Use the
full held-out benchmark evaluations for that purpose.
