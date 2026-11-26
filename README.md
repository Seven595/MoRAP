# MoRAP

**Decoupling expression readout from morphological aggregation for histology-based spatial gene expression prediction**

MoRAP (morphology-guided readout and propagation) predicts spatial gene
expression from histology images in two stages:

1. **Expression readout.** A unit-balanced linear model maps frozen pathology
   descriptors to spot-level expression predictions.
2. **Morphological neighbour propagation (MNP).** A graph constructed from
   contextual and local descriptor similarities aggregates these predictions
   without refitting the readout. Neighbours are selected by normalised Borda
   rank fusion, and their predictions are combined using softmax weights.

For a matrix of spot-level predictions $\hat{Y}_{\mathrm{point}}$, propagation
is $\hat{Y}_{\mathrm{MNP}} = A\hat{Y}_{\mathrm{point}}$, where $A$ is a
row-stochastic matrix computed from image descriptors. Graph construction and
propagation do not require expression measurements from the predicted sections.

This repository provides the reference cSCC implementation, within-section
propagation operators, and scripts for benchmark evaluation and figure
preparation. The available workflows and their data requirements are described
in [REPRODUCTION.md](REPRODUCTION.md).

## Installation

Python 3.10 or newer is required. The core package depends on NumPy and PyTorch.
CPU execution is supported; a compatible CUDA-enabled PyTorch installation can
be used for the ridge solve.

```bash
git clone https://github.com/Seven595/MoRAP.git
cd MoRAP
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Install additional dependencies for analyses or figures as needed:

| Workflow | Installation |
|---|---|
| Core model and tests | `python -m pip install -e .` |
| Benchmark analyses | `python -m pip install -e ".[analysis]"` |
| Analyses and figure generation | `python -m pip install -e ".[analysis,figures]"` |

Comparator methods require their own environments and pretrained weights. See
[comparators/README.md](comparators/README.md) for their implementations and
[THIRD_PARTY.md](THIRD_PARTY.md) for source and license information.

## Minimal example

The synthetic example runs the ridge readout and cross-section propagation on
deterministic random descriptors. It requires no external data and checks the
numerical workflow; its output is not a biological performance evaluation.

```bash
python examples/minimal.py
```

Expected output:

```text
pointwise shape: (195, 5)
MoRAP shape:     (195, 5)
finite output:   True
```

## Data and path configuration

The cSCC workflow uses prepared expression matrices, patch-index metadata, and
frozen contextual and local CTransPath descriptors. Cohort data, pretrained
weights, descriptor caches, and saved benchmark predictions are not included
in this repository. The input formats are described in
[morap/README.md](morap/README.md#input-data).

Configure the directories before running the data-dependent workflows:

```bash
export MORAP_DATA_ROOT="$PWD/data"
export MORAP_CACHE_ROOT="$MORAP_DATA_ROOT/cache"
export MORAP_RESULTS_ROOT="$PWD/outputs"
export MORAP_ARCHIVE_ROOT="$MORAP_DATA_ROOT/archive"
export MORAP_MODEL_ROOT="$MORAP_DATA_ROOT/models"
```

| Variable | Contents | Default |
|---|---|---|
| `MORAP_DATA_ROOT` | Cohort data and expression matrices | `<repository>/data` |
| `MORAP_CACHE_ROOT` | Descriptor and patch caches | `<data root>/cache` |
| `MORAP_RESULTS_ROOT` | Checkpoints, predictions, metrics, and figures | `<repository>/outputs` |
| `MORAP_ARCHIVE_ROOT` | Saved benchmark results and supporting analysis files | `<data root>/archive` |
| `MORAP_MODEL_ROOT` | Pretrained model weights | `<data root>/models` |

Relative paths are resolved from the working directory. The variables specify
where prepared inputs are located; they do not download or generate those
inputs. [configs/paths.example.yaml](configs/paths.example.yaml) provides a
configuration example.

## Reference cSCC workflow

The reference model uses 768-dimensional contextual CTransPath descriptors, a
patient-balanced ridge readout, and one cross-section MNP step. The fixed
configuration uses ridge regularisation $\lambda=10^6$, 64 neighbours per
other section, and softmax inverse temperature 10. Each eligible section
receives equal total aggregation weight.

The [four patient folds](morap/configs/cscc_patient_cv4.json) cover 12 sections
from four patients and a fixed ordered panel of 997 genes. Each fold specifies
two training patients, one validation patient, and one test patient. The
reference model uses fixed hyperparameters and fits only the two training
patients; it does not use validation expression for fitting or selection.

After preparing the inputs, train and evaluate all four folds:

```bash
for fold in 0 1 2 3; do
  morap train --fold "$fold" --device cpu
done
morap evaluate
```

Use `--device cuda:0` to run the ridge solve on a GPU. Training writes the
checkpoint and outer-test predictions under
`$MORAP_RESULTS_ROOT/cscc/folds/fold<FOLD_ID>/`. Evaluation checks file hashes,
input manifests, and spot/gene alignment before scoring the predictions.
The commands refuse to overwrite an existing fold directory or evaluation file.

### Prediction on prepared sections

```bash
morap infer \
  --checkpoint "$MORAP_RESULTS_ROOT/cscc/folds/fold0/checkpoint.pt" \
  --sections SECTION_1 SECTION_2 SECTION_3 \
  --output "$MORAP_RESULTS_ROOT/inference/predictions.npz"
```

Replace the section identifiers with entries in the configured descriptor
cache. This command uses the cross-section reference model: sections must
belong to one patient, and at least two sections with at least 64 spots each
are required. It reads the fitted checkpoint and image descriptors without
opening expression labels for the requested sections. For single-section
propagation, use [`morap.within_section.apply`](morap/within_section.py), as
described in [the implementation guide](morap/README.md#within-section-propagation).

### Expression targets and evaluation

The reference cSCC readout is fitted to `log1p(raw counts)`, standardised
separately for each gene within each training section. Its predictions are
in this standardised target space, rather than absolute counts.

The evaluator computes gene-wise Pearson correlation coefficients (PCC) within
each section, averages over genes and sections within each test patient, and
then averages equally over the four patients. For nonconstant genes, positive
affine rescaling of the measured target within a section leaves PCC unchanged
for fixed predictions. Mean squared error (MSE) is evaluated against
section-standardised targets and depends on that scale. Target transformations
and aggregation rules for other workflows are detailed in
[REPRODUCTION.md](REPRODUCTION.md#expression-targets-and-scoring).

## Repository organisation

| Location | Contents |
|---|---|
| [`morap/`](morap/) | Reference model, propagation operators, evaluation utilities, and analyses |
| [`experiments/`](experiments/) | Comparator benchmarks, component analyses, and propagation experiments |
| [`plotting/`](plotting/) | Framework, attribution, benchmark-composite, and spatial-map builders |
| [`comparators/`](comparators/) | Comparator adapters and third-party source snapshots |
| [`examples/`](examples/) | Synthetic example |
| [`tests/`](tests/) | Numerical, artifact-reading, and path checks |
| [`REPRODUCTION.md`](REPRODUCTION.md) | Workflow commands, required inputs, and evaluation protocols |

## Validation

```bash
python -m unittest discover -s tests -v
```

The tests cover patient weighting, the ridge solve, graph normalisation,
propagation behaviour, and prediction-file validation. Reproducing biological
results additionally requires the corresponding data, descriptors, predictions,
and evaluation settings.
