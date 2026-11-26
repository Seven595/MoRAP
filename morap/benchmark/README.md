# Benchmark evaluation utilities

These modules define data loading, target transformations, prediction
alignment, and metric aggregation used by the comparator adapters.

| File | Role |
|---|---|
| [`benchmark_external.py`](benchmark_external.py) | cSCC folds, slides, 997-gene panel, patch caches, target transforms, and external dataset configurations |
| [`hespotex_metrics.py`](hespotex_metrics.py) | HESpotEx gene-wise metrics |
| [`metrics.py`](metrics.py) | Spatial expression metrics, including PCC, MI, SSIM, and AUC |
| [`evaluator.py`](evaluator.py) | Section/gene metrics, patient-level aggregation, and patient-bootstrap intervals |

Training targets and scoring references are specified separately for each
analysis. The matched-descriptor comparisons use a common log-transformed
raw-count reference. Complete cSCC pipeline comparisons retain method-specific
target transformations. Paired MNP evaluations keep each predictor's scoring
target fixed before and after propagation. See
[REPRODUCTION.md](../../REPRODUCTION.md#expression-targets-and-scoring).

Install MoRAP before launching an adapter so that `morap.benchmark` is
available in its Python environment.
