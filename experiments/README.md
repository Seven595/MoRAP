# Experiments

| Directory | Purpose |
|---|---|
| [`component_analysis/`](component_analysis/) | Comparison of encoders, image fields of view, and prediction modules under specified evaluation protocols |
| [`neighbor_controls/`](neighbor_controls/) | Morphological, spatial, and random-neighbour propagation controls |
| [`transfer/`](transfer/) | Within-section MNP applied to saved predictions for HEST, STImage, and HESpotEx-aligned cSCC and HER2+ datasets |
| [`benchmarks/`](benchmarks/) | Comparator training and evaluation workflows |

Run scripts from the repository root in an environment with the required
method dependencies. Data, descriptor caches, and saved prediction files are
configured through `MORAP_*` paths. Some workflows also load analysis helpers
from `MORAP_ARCHIVE_ROOT`. Consult
[REPRODUCTION.md](../REPRODUCTION.md) for commands and required inputs.
