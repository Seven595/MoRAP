# MoRAP

MoRAP (morphology-guided readout and propagation) predicts spatial gene
expression from H&E images with a
patient-balanced linear readout followed by one training-free morphological
neighbour propagation (MNP) step. The graph uses frozen contextual and local
image descriptors; no expression measurement from a predicted section is used
to construct the graph.

This repository contains the reference cSCC implementation, manuscript
analyses, figure builders, and protocol adapters used to compare published
methods under common evaluation contracts.

Manuscript: **MoRAP: Decoupling expression readout from morphological aggregation
for histology-based spatial gene expression prediction**.

Repository: [Seven595/MoRAP](https://github.com/Seven595/MoRAP).

## Quick start

Python 3.10 or newer is required. CUDA is optional for the reference method;
CPU execution is sufficient for the synthetic example and tests.

```bash
git clone https://github.com/Seven595/MoRAP.git
cd MoRAP
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python examples/minimal.py
```

The example is deterministic, requires no downloaded data, and should report:

```text
pointwise shape: (195, 5)
MoRAP shape:     (195, 5)
finite output:   True
```

Run the test suite with:

```bash
python -m unittest discover -s tests -v
```

## Upgrading from the previous name

The project was previously named Lin-MNP. Reinstall with
`python -m pip install -e .` after updating your checkout. The current package
and command are both `morap`; update Python imports and shell scripts accordingly.

| Interface | Current name | Historical name |
|---|---|---|
| Python package | `morap` | `lin_mnp` |
| CLI | `morap` | `lin-mnp` |
| Environment prefix | `MORAP_` | `LIN_MNP_` |
| Prediction array / method ID | `morap` | `lin_mnp` |
| Checkpoint model identity | `MoRAP` | `Lin-MNP` |

New artifacts use the current names. Readers accept historical prediction keys,
checksum fields, checkpoint identities, and method directories in the companion
bundle without modifying the original files or their hashes. Historical
environment variables remain a fallback; explicitly set `MORAP_*` values take
precedence. Old package imports and the old CLI are not installed as aliases.
MNP still denotes **morphological neighbour propagation**, the propagation
component of MoRAP. Earlier archived comparator branches such as PACE-ST retain
their own identities.

## Installation profiles

The base package contains only the dependencies needed by the reference
numerical core. Install optional dependencies for the workflows you intend to
run:

| Use case | Command |
|---|---|
| Reference model, inference, tests | `python -m pip install -e .` |
| Analyses and benchmark contracts | `python -m pip install -e ".[analysis]"` |
| Manuscript figures | `python -m pip install -e ".[analysis,figures]"` |
| Core package via requirements file | `python -m pip install -r requirements.txt` |

For a CUDA run, install the PyTorch build matching the local driver before
installing MoRAP. Comparator dependencies are deliberately not part of the
base environment because published methods require mutually incompatible
versions. Use the environment documented by each source under
`comparators/methods/`; the HESpotEx snapshot includes a reduced, portable
requirements file.

## Data and path configuration

No machine-specific absolute path is embedded in the code. All data, cache,
model, artifact, and result roots are controlled by environment variables.
Relative values are resolved from the directory where the command is launched.

```bash
export MORAP_DATA_ROOT="$PWD/data"
export MORAP_CACHE_ROOT="$PWD/data/cache"
export MORAP_RESULTS_ROOT="$PWD/outputs"
export MORAP_ARCHIVE_ROOT="$PWD/artifacts"
export MORAP_MODEL_ROOT="$PWD/models"
```

| Variable | Purpose | Default when unset |
|---|---|---|
| `MORAP_DATA_ROOT` | Cohorts, labels, and derived inputs | `./data` at the repository root |
| `MORAP_CACHE_ROOT` | Frozen descriptors and patch caches | `$MORAP_DATA_ROOT/cache` |
| `MORAP_RESULTS_ROOT` | Checkpoints, predictions, tables, and figures | `./outputs` at the repository root |
| `MORAP_ARCHIVE_ROOT` | Companion manuscript artifact bundle | `$MORAP_DATA_ROOT/archive` |
| `MORAP_MODEL_ROOT` | Downloaded pretrained weights | `$MORAP_DATA_ROOT/models` |

The values above are examples, not a required layout. A machine-readable
example and the minimum expected cSCC tree are in
[`configs/paths.example.yaml`](configs/paths.example.yaml). Large cohorts,
weights, descriptor caches, predictions, and the companion artifact bundle are
not committed to Git.

Minimum cSCC inputs:

```text
$MORAP_DATA_ROOT/
└── cscc/
    └── labels/
$MORAP_CACHE_ROOT/
└── cscc/
    ├── raw_patches/
    ├── ctranspath_context/
    └── ctranspath_local/
```

Raw cohort images and geometry are needed only when rebuilding the descriptor
caches or rendering image-based figures.

## Reference cSCC workflow

Fit the four patient-held-out folds. The fixed split is stored in
[`morap/configs/cscc_patient_cv4.json`](morap/configs/cscc_patient_cv4.json).

```bash
for fold in 0 1 2 3; do
  morap train --fold "$fold" --device cpu
done
morap evaluate
```

Use `--device cuda:0` to reproduce the GPU execution setting. Training writes
pointwise and MoRAP predictions without opening the outer-test labels. The
separate evaluation command verifies every fold artifact before loading those
labels. Existing completed fold directories are never overwritten.

Label-free inference from a fitted checkpoint is:

```bash
morap infer \
  --checkpoint outputs/cscc/folds/fold0/checkpoint.pt \
  --sections SECTION_1 SECTION_2 SECTION_3 \
  --output outputs/inference/predictions.npz
```

Cross-section MoRAP requires at least two sections from one patient. For a
single section, use the operators in
[`morap/within_section.py`](morap/within_section.py).

## Reproducing manuscript tables and figures

Install the analysis and figure extras and configure the five roots above.
Most table and figure workflows additionally require the companion bundle at
`MORAP_ARCHIVE_ROOT`.

The main figure entry points are:

```bash
python plotting/manuscript/make_framework_figure.py
python plotting/manuscript/make_attribution_figure.py
python plotting/manuscript/make_benchmark_figure.py
python plotting/spatial_maps/build_cscc_spatial_expression_overviews.py
python plotting/spatial_maps/build_hest_stimage_spatial_expression_overviews.py
```

Outputs are written under `$MORAP_RESULTS_ROOT/figures/` by default; every
builder accepts `--output` for an explicit destination. The full
manuscript-to-command map, table workflows, required inputs, and expected
outputs are documented in [`REPRODUCTION.md`](REPRODUCTION.md).

## Repository layout

```text
MoRAP/
├── morap/                    # Installable reference package
│   ├── model.py              # Ridge readout, MNP, and CLI
│   ├── within_section.py     # Single-section propagation operators
│   ├── paths.py              # Environment-controlled path policy
│   ├── benchmark/            # Fold, target, and metric contracts
│   └── analysis/             # Supplementary analyses
├── experiments/              # Manuscript experiment entry points
│   ├── benchmarks/           # cSCC, HEST, STImage, and HESpotEx
│   ├── component_analysis/   # Encoder/downstream attribution
│   ├── neighbor_controls/    # Neighbour controls
│   └── transfer/             # Cross-benchmark MNP transfer
├── plotting/                 # Main and spatial-map figure builders
├── comparators/
│   ├── adapters/             # Common-contract wrappers
│   └── methods/              # Vendored upstream source snapshots
├── examples/                 # Data-free minimal example
├── configs/                  # Split and path examples
├── tests/                    # Numerical and portability tests
├── REPRODUCTION.md           # Detailed paper reproduction guide
└── THIRD_PARTY.md            # Upstream provenance and licensing
```

The installable package does not expose a generic top-level `shared` module;
benchmark utilities live under `morap.benchmark`. Vendored upstream code is
marked as such for GitHub language statistics and remains governed by its
original license.

## Expression target and integrity notes

The primary cSCC readout fits the ordered 997-gene `log1p(raw counts)` matrix
after within-section, per-gene standardisation of each training section.
Predictions remain in that standardised space. Gene-wise PCC computed within a
section is unchanged by the corresponding positive affine target transform;
MSE is reported in standardised space.

Reference outputs record source, checkpoint, prediction, and array hashes.
Loaders validate cache provenance, barcode order, gene order, shapes, and
SHA-256 checksums. See
[`REPRODUCTION.md`](REPRODUCTION.md#expression-targets-and-scoring) for the
target used by each comparison.
