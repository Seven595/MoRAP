# Reference implementation

[`model.py`](model.py) implements the cSCC patient-balanced ridge readout,
cross-section morphological neighbour propagation (MNP), and the `morap`
command-line interface.

## Linear readout

For *N* training spots from a set of patients *U*, each spot receives weight:

```math
w_i = \frac{N}{|U|\,n_{u(i)}}
```

The denominator combines the number of training patients with the number of
spots from the patient containing spot *i*. Each patient therefore contributes
equal total weight to the fit. Feature means and variances and the target mean
are computed with these weights. The readout solves multi-output ridge
regression with regularisation `1e6` on the centred, standardised features and
centred targets.

The cSCC model uses 768-dimensional contextual CTransPath descriptors.
Training targets are `log1p(raw counts)`, standardised within each section
and gene. The checkpoint stores the feature transformation, target mean,
and ridge coefficients used for prediction.

## Cross-section propagation

Contextual and local descriptors are L2-normalised. For each query spot,
cosine similarities are ranked separately within each other section.
Normalised Borda fusion assigns equal weight to contextual and local ranks.
The 64 highest-scoring neighbours from each other section receive softmax
weights with inverse temperature 10. Weights are then divided by the number
of other sections, giving each section equal total mass. One propagation
step aggregates the readout predictions using this graph.

The command-line workflow requires at least two sections from one patient,
with at least 64 spots per section. These are the requirements of the fixed
cSCC implementation. The within-section operator below uses a separately
specified neighbour count.

## Input data

Paths are configured through [`paths.py`](paths.py). The reference workflow
expects:

| Location | Required contents |
|---|---|
| `$MORAP_DATA_ROOT/cscc/labels/<section>.npz` | `barcodes`, `genes`, scalar `patient_id`, and a spot-by-gene `log1p_raw_counts` matrix |
| `$MORAP_CACHE_ROOT/cscc/raw_patches/` | `manifest.json` and its referenced index CSV, including `section`, `patient`, `barcode`, and `global_index` columns |
| `$MORAP_CACHE_ROOT/cscc/ctranspath_context/` | `manifest.json` and its referenced pooled 768-dimensional descriptor matrix |
| `$MORAP_CACHE_ROOT/cscc/ctranspath_local/` | `manifest.json` and its referenced pooled 768-dimensional descriptor matrix |

Descriptor rows follow the patch index. The loaders check cache provenance,
array shapes, available checksums, barcode alignment, and the ordered 997-gene
panel specified by `model.CONFIG`. Manifests must describe the source views
(context: 384 pixels resized to 224; local: 224 pixels) and descriptor files.
The exact manifest fields and checks are defined by `LabeledSpotDataset`,
`InferenceSpotDataset`, and `load_local_cache` in [`model.py`](model.py).
Creating directories alone does not prepare these inputs.

## Training and evaluation

Run from the repository root after installation and input preparation:

```bash
for fold in 0 1 2 3; do
  morap train --fold "$fold" --device cpu
done
morap evaluate
```

Each fold writes `checkpoint.pt`, `outer_test_predictions.npz`,
`run_metadata.json`, and `complete.json`. The prediction archive contains
`pointwise` and `morap` matrices together with section, barcode, and gene
identifiers. The evaluator writes `evaluation.json` after checking all four
folds. Test expression is opened only in the evaluation phase.

Predictions retain the section-standardised expression scale. PCC is computed
within section and gene, then averaged equally across genes, sections within
a patient, and patients. The cSCC evaluator assigns zero PCC where the
correlation denominator is at most `1e-12`. MSE is reported in the
section-standardised target space.

## Within-section propagation

[`within_section.py`](within_section.py) applies MNP to an existing prediction
matrix using neighbours from the same section. The query spot is excluded
from the selected neighbours, and the requested count is capped at the
number of other spots.

```python
from morap.within_section import apply

# prediction: [spots, genes]; context and local: [spots, descriptor dimensions]
# All three arrays must have the same spot order and refer to one section.
propagated, effective_k = apply(
    prediction,
    context,
    local,
    neighbour_count=128,
    fusion="borda",
    weighting="softmax",
)
```

`prediction` contains fitted model outputs, not measured expression.
The operator does not refit the predictor or require expression labels.
