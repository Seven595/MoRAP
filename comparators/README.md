# Comparator implementations

[`methods/`](methods/) contains third-party source snapshots.
[`adapters/`](adapters/) contains training, feature-extraction, and evaluation
wrappers for the dataset splits and gene panels used in the experiments.
Source locations and licensing information are listed in
[THIRD_PARTY.md](../THIRD_PARTY.md).

Install MoRAP in each adapter environment so that `morap.benchmark` and
`morap.paths` can be imported. Each comparator also requires its own
method-specific dependencies, input data, and pretrained weights.

Additional implementations used by the benchmark are located at:

- **HoloTea:** [`experiments/benchmarks/train_additional_comparators.py`](../experiments/benchmarks/train_additional_comparators.py).
- **STAG:** [`experiments/benchmarks/run_cscc_additional_comparators.py`](../experiments/benchmarks/run_cscc_additional_comparators.py) and [`experiments/benchmarks/train_additional_comparators.py`](../experiments/benchmarks/train_additional_comparators.py). Encoder checkpoint instructions are in [`methods/STAG/README.md`](methods/STAG/README.md).
- **HisToGene:** [`methods/mclSTExp/baselines/HisToGene/`](methods/mclSTExp/baselines/HisToGene/).

Dataset splits, target transformations, and checkpoint selection settings
must be matched to the intended comparison. Sharing a gene panel alone does
not make results from different training or scoring protocols equivalent.
