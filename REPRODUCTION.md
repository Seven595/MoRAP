# Reproducing the manuscript

Run all commands from the repository root after installing the required profile
and setting the path variables described in the main
[`README.md`](README.md#data-and-path-configuration).

## Scope and required inputs

This guide documents the workflows implemented in this checkout. The
synthetic example and numerical tests require only the core package. The
cSCC training and evaluation commands require prepared data and descriptor
caches. Benchmark analyses and figure builders additionally use saved
predictions, summary tables, or supporting scripts under `MORAP_ARCHIVE_ROOT`.

| Workflow | Required inputs beyond the installed package |
|---|---|
| Synthetic example and unit tests | None |
| cSCC reference training and evaluation | Label matrices, patch index, contextual and local CTransPath caches, and their manifests |
| Comparator training | Cohort data, split and gene-panel definitions, method-specific dependencies, and pretrained weights |
| Propagation analyses | Saved base predictions, matching descriptors, and the corresponding scoring targets |
| Figure generation | The source data, tables, images, or pre-rendered panels required by the selected builder |

The repository does not include the large data files or the analysis archive,
and it does not currently specify a download location for that archive.
The commands below assume those inputs have been prepared in the indicated
locations. The NCCHE and DeepSpot experiments described in the manuscript do
not have dedicated execution scripts in this checkout; the listed commands
should not be interpreted as complete coverage of those experiments.

## 1. Reference cSCC result

Required inputs are the cSCC expression matrices, raw-patch index, and
contextual and local CTransPath descriptor caches. Their formats are described
in [morap/README.md](morap/README.md#input-data), and the directory configuration
is illustrated in [configs/paths.example.yaml](configs/paths.example.yaml).

```bash
for fold in 0 1 2 3; do
  morap train --fold "$fold" --device cuda:0
done
morap evaluate
```

Use `--device cpu` when CUDA is unavailable. The training phase fits only the
two training patients. It does not open validation or outer-test expression.
The evaluation phase verifies all four prediction artifacts before opening the
test targets and applies equal patient weighting.

Each `fold<FOLD_ID>/` directory under `$MORAP_RESULTS_ROOT/cscc/folds/`
contains `checkpoint.pt`, `outer_test_predictions.npz`, `run_metadata.json`,
and `complete.json`. Evaluation writes `evaluation.json` in the parent
directory. Predictions remain in the section-standardised target space.
Training refuses to overwrite an existing fold directory, and evaluation
refuses to overwrite an existing `evaluation.json`.

## 2. Benchmark and propagation workflows

### HEST and STImage comparator benchmarks

Prepare the HEST data under `$MORAP_DATA_ROOT/hest` and STImage data under
`$MORAP_DATA_ROOT/stimage`. The STImage workflow also reads protocol files
from `$MORAP_ARCHIVE_ROOT/stimage/protocol` and targets from
`$MORAP_DATA_ROOT/stimage/targets`. Generate image patch caches and dataset
configurations, including split and gene-panel definitions:

```bash
python experiments/benchmarks/prepare_hest_stimage_comparator_contracts.py \
  --stage all
```

Cache the representation required by a comparator when needed. For example:

```bash
python experiments/benchmarks/run_hest_stimage_benchmarks.py \
  cache --kind egn50 --gpu 0
```

Run and independently evaluate one method at a time:

```bash
python experiments/benchmarks/run_hest_stimage_benchmarks.py \
  run --method METHOD_ID --gpus 0 --epochs 30 --threads 4

python experiments/benchmarks/run_hest_stimage_benchmarks.py \
  evaluate --method METHOD_ID
```

Use `--help` to list the supported method IDs and cache kinds. Comparator
environments and weights are method-specific; see
[`comparators/README.md`](comparators/README.md) and
[`THIRD_PARTY.md`](THIRD_PARTY.md).

### Within-section MNP on saved predictions

The HEST and STImage scripts apply within-section MNP to saved readout
predictions for CTransPath and UNI-v1. They read base predictions from
`$MORAP_ARCHIVE_ROOT/legacy/development/transfer/{hest,stimage}/` and matching
descriptors from `$MORAP_CACHE_ROOT/{hest,stimage}/`. These scripts evaluate
propagation on those files; they do not train the base readouts.

```bash
for encoder in ctranspath uni_v1; do
  python experiments/transfer/run_hest_within_section.py --encoder "$encoder"
  python experiments/transfer/run_stimage_within_section.py --encoder "$encoder"
done
```

The HESpotEx-aligned cSCC and HER2+ workflow reads base readout predictions
under `$MORAP_ARCHIVE_ROOT/hespotex/morap`, dataset configurations under
`$MORAP_ARCHIVE_ROOT/hespotex/contracts`, and expression/descriptor files
under `$MORAP_DATA_ROOT/{cscc,her2}/derived`. These section-level experiments
use different gene panels and splits from the 997-gene cSCC reference:

```bash
for cohort in cscc her2; do
  python experiments/transfer/run_hespotex_within_section.py build --cohort "$cohort"
  python experiments/transfer/run_hespotex_within_section.py evaluate --cohort "$cohort"
  python experiments/transfer/run_hespotex_within_section.py metrics --cohort "$cohort"
done
```

### Cross-section MNP on cSCC comparator predictions

The comparator analysis uses the reference cSCC checkpoints and predictions,
the index at
`$MORAP_ARCHIVE_ROOT/detail/01_benchmark/comparators_historical/benchmark_prediction_artifact_index.csv`,
and the baseline metric table at
`$MORAP_ARCHIVE_ROOT/benchmark_strict/per_patient_gene_metrics.csv.gz`:

```bash
python -m morap.analysis.evaluate_comparator_transfer
```

The analysis builds one descriptor graph per held-out patient and applies
it to the readout and available comparator predictions. Each paired comparison
keeps the fitted predictor and scoring target fixed. Comparator predictions
are standardised within section and gene before propagation; an additional
unstandardised propagation result is reported. The evaluated method set is
determined by the prediction index and coverage across all four folds.
`summary.json` records methods without full section coverage, and
`summary.csv` reports the included methods and their paired PCC changes.

### cSCC comparator metrics

This evaluator reads comparator predictions under
`$MORAP_ARCHIVE_ROOT/benchmark/`, cSCC labels, saved STFlow results, and the
metric helper `$MORAP_ARCHIVE_ROOT/tools/compute_unified_protocol_metrics.py`:

```bash
python experiments/benchmarks/evaluate_cscc_added_benchmark_metrics.py
```

The script writes its tables below
`$MORAP_RESULTS_ROOT/additional_comparators/cscc/evaluation/` unless
`--output` is supplied.

## 3. Figure workflows

Install the figure extras first:

```bash
python -m pip install -e ".[analysis,figures]"
```

### Framework overview

Requires cSCC H&E images, geometry, labels, and both CTransPath descriptor
views:

```bash
python plotting/manuscript/make_framework_figure.py \
  --output "$MORAP_RESULTS_ROOT/figures/figure1.png"
```

### Matched-descriptor attribution

Requires
`$MORAP_ARCHIVE_ROOT/reports/comparator_results/benchmark_common_contract_attribution.csv`:

```bash
python plotting/manuscript/make_attribution_figure.py \
  --output "$MORAP_RESULTS_ROOT/figures/figure2.png"
```

Component-analysis workflows are in `experiments/component_analysis/`.
The following entry points prepare image caches, fit matched readouts, and
run downstream modules; they require the corresponding cohort data and
encoder descriptors:

```bash
python experiments/component_analysis/prepare_benchmark_384_patch_cache.py
python experiments/component_analysis/run_benchmark_common_ctranspath_ridge.py \
  --scale 384
python experiments/component_analysis/run_benchmark_common_original_downstream.py \
  --method METHOD_ID --fold FOLD_ID --device cuda:0
```

Some encoder-specific attribution scripts also load helpers from
`MORAP_ARCHIVE_ROOT`. The plotting command above reads an existing CSV;
it does not execute these training workflows.

### Benchmark end-point composite

Requires three pre-rendered source panels under
`$MORAP_ARCHIVE_ROOT/figures/benchmark/panels/`:
`benchmark_fig2d_cscc_strict.png`, `benchmark_fig3a_cscc_strict.png`, and
`benchmark_fig3d_cscc_strict.png`. This script assembles those images into a
composite; it does not recompute the benchmark statistics.

```bash
python plotting/manuscript/make_benchmark_figure.py \
  --output "$MORAP_RESULTS_ROOT/figures/supplementary_benchmark_endpoints.png"
```

### Spatial-expression maps

The cSCC/HER2+ builder requires saved predictions, metric tables, tissue
images, and plotting helpers under `$MORAP_ARCHIVE_ROOT/spatial_maps/legacy`.
The HEST/STImage builder requires cohort images and geometry, comparator
predictions under `$MORAP_ARCHIVE_ROOT/benchmarks/hest_stimage`, and readout
predictions under `$MORAP_ARCHIVE_ROOT/transfer/{hest,stimage}/uni_v1`.

```bash
python plotting/spatial_maps/build_cscc_spatial_expression_overviews.py \
  --output "$MORAP_RESULTS_ROOT/figures/spatial_maps" \
  --dpi 220 --workers 4

python plotting/spatial_maps/build_hest_stimage_spatial_expression_overviews.py \
  --output "$MORAP_RESULTS_ROOT/figures/spatial_maps" \
  --dpi 220
```

Both builders check prediction alignment and stored metric values. Gene
selection uses observed prediction performance, so the maps are descriptive
examples rather than estimates of aggregate model accuracy. See
[plotting/spatial_maps/README.md](plotting/spatial_maps/README.md).

## 4. Supplementary analyses

| Analysis | Command |
|---|---|
| Encoder transfer | `python -m morap.analysis.evaluate_encoder_transfer --device cuda:0` |
| Neighbour accuracy sensitivity | `python -m morap.analysis.analyze_accuracy_sensitivity` |
| Propagation depth | `python -m morap.analysis.analyze_diffusion_depth` |
| Descriptor graph views | `python -m morap.analysis.analyze_graph_views` |
| Within-section controls | `python experiments/neighbor_controls/run_within_section_control.py train-fold --fold FOLD_ID` |
| Control aggregation | `python experiments/neighbor_controls/run_within_section_control.py evaluate` |
| Single-fold efficiency | `python experiments/benchmarks/run_cscc_single_fold_efficiency.py --help` |

## Workflow index

| Workflow | Primary entry point |
|---|---|
| cSCC linear readout and MoRAP | `morap train`, then `morap evaluate` |
| HEST and STImage benchmark table | `experiments/benchmarks/run_hest_stimage_benchmarks.py` |
| Benchmark and encoder transfer | `experiments/transfer/run_{hest,stimage,hespotex}_within_section.py` |
| Comparator transfer | `python -m morap.analysis.evaluate_comparator_transfer` |
| Framework figure | `plotting/manuscript/make_framework_figure.py` |
| Attribution figure | `plotting/manuscript/make_attribution_figure.py` |
| Benchmark composite | `plotting/manuscript/make_benchmark_figure.py` |
| Spatial maps | `plotting/spatial_maps/` |
| Component attribution | `experiments/component_analysis/` |
| Neighbour controls | `experiments/neighbor_controls/` |
| Runtime analysis | `experiments/benchmarks/run_cscc_single_fold_efficiency.py` |

## Expression targets and scoring

Training targets and scoring references serve different roles:

| Analysis | Training targets | PCC scoring reference |
|---|---|---|
| Native modules on matched cSCC descriptors | Ordered 997-gene `log1p(raw counts)` | Common `log1p(raw counts)` within section |
| Readouts paired with method-specific representations | Same unstandardised `log1p(raw counts)` | Same common expression reference |
| Primary CTransPath-384 readout | `log1p(raw counts)` standardised within each training section and gene | Same common expression reference; section-standardised labels give identical PCC |
| Complete cSCC pipelines | Method-specific target transformations | Each method's own target space |
| HEST and STImage comparator workflows | Method-specific transforms of the deposited 50-gene targets, recorded in run metadata | Common deposited `log1p(raw counts)` for the main comparisons; inspect the recorded target space for separately standardised runs |
| Cross-section MNP on cSCC comparator predictions | Base predictors are not refitted | Each predictor's target transformation from run metadata, fixed before and after MNP |

For each cSCC comparator MNP pair, predictions are standardised within section and
gene before propagation, the same measured-expression target is retained for
both scores, and the base predictor is unchanged. Linear-readout transfer
analyses likewise retain each benchmark's target before and after MNP.

For nonconstant genes, a positive affine transformation of the scoring target
leaves PCC unchanged for fixed predictions within a section. Applying
section-specific transforms before fitting can change the fitted predictor, and applying them before
pooling sections can change pooled PCC. Per-spot library-size normalisation
(CP10K or CPM) changes the scoring reference rather than merely changing its
units.

## Validation and reporting

Run `python -m unittest discover -s tests -v` to check the numerical core
and artifact readers. For cSCC reference results, `morap evaluate` verifies
completion records, file hashes, input manifests, and prediction alignment.
Third-party source checksums can be checked from the repository root with
`(cd comparators/methods && shasum -a 256 -c MANIFEST.sha256)`.

When reporting benchmark results, record the code revision, data and gene
panel, split identifiers, encoder and preprocessing, target transformation,
checkpoint selection rule, and metric aggregation. Record the software
versions, hardware, and command line for computational reproducibility.
The available tests do not replace a rerun of the data-dependent experiments.
