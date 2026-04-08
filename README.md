# wkanno

`wkanno` is a standalone Python CLI for downloading WebKnossos annotation metadata,
the matching raw image patch, and aligned label volumes for local evaluation workflows.

It exists to make a validated lab workflow easy to reuse without depending on the
current `webknossos` Python client, which can fail against servers exposing older API
versions.

## What It Does

- Inspects an annotation through the WebKnossos REST API.
- Downloads the full annotation archive.
- Extracts the annotation volume archive locally.
- Downloads the matching raw patch from the linked dataset.
- Reconstructs aligned label, binary, and valid-mask arrays.
- Optionally exports local `.npy` volumes to NIfTI for viewers such as Niivue.

## Installation

### Recommended: install as a CLI tool

```bash
pipx install /path/to/wkanno
```

After the repository is published, the same flow becomes:

```bash
pipx install git+https://github.com/gaiborjosue/wkanno.git
```

If `pipx` is not available, use a dedicated environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install /path/to/wkanno
```

## Authentication

Set your WebKnossos token in the environment:

```bash
export WEBKNOSSOS_TOKEN=your_token_here
```

You can also pass `--token` explicitly to any command.

## Typical User Flow

For most users, the end-to-end workflow is:

```bash
export WEBKNOSSOS_TOKEN=your_token_here
wkanno list-boxes 6982650e010000a3019f7143
wkanno fetch-box 6982650e010000a3019f7143 'WM 2' --output-dir ./wkanno_out --export-nifti
```

That is enough to:

- discover the available annotator-defined box names
- download the linked annotation archive
- fetch the matching raw patch from the dataset
- reconstruct aligned labels, binary mask, and valid mask
- export viewer-friendly NIfTI volumes when requested

## Quick Start

List the available named boxes first:

```bash
wkanno list-boxes 6982650e010000a3019f7143
```

Then fetch one specific box exactly by name:

```bash
wkanno fetch-box 6982650e010000a3019f7143 'WM 2' \
  --output-dir ./wkanno_out \
  --export-nifti
```

Fetch everything needed for a named user bounding box:

```bash
wkanno fetch-box 696148730100001001be9620 WM \
  --output-dir ./wkanno_out \
  --export-nifti
```

This writes:

- `annotation_<id>/...` with the summary JSON and annotation archive
- `<annotation>_<box>.npy` for the raw patch
- `<annotation>_<box>_labels.npy`
- `<annotation>_<box>_binary.npy`
- `<annotation>_<box>_valid_mask.npy`
- optional NIfTI exports under `nifti/`

## Command Overview

Inspect an annotation:

```bash
wkanno inspect 696148730100001001be9620 --download full --extract --output-dir ./annotation_bundle
```

List the available box names in a user-friendly format:

```bash
wkanno list-boxes 6982650e010000a3019f7143
```

This is the easiest way to discover names like `WM 1`, `WM 2`, or
`White-Gray Transition` before calling `fetch-box`.

Download a raw patch for one named box from an existing summary JSON:

```bash
wkanno download-raw \
  --annotation-summary ./annotation_bundle/696148730100001001be9620_summary.json \
  --box-name WM \
  --output ./macaque_NEFH_WM.npy
```

Extract aligned label products from an extracted annotation archive and patch metadata:

```bash
wkanno extract-labels \
  --annotation-dir ./annotation_bundle \
  --patch-meta ./macaque_NEFH_WM.npy.meta.json \
  --box-name WM \
  --output-prefix ./macaque_NEFH_WM
```

Export `.npy` arrays to NIfTI:

```bash
wkanno export-nifti \
  --inputs ./macaque_NEFH_WM.npy ./macaque_NEFH_WM_binary.npy \
  --output-dir ./nifti \
  --voxel-size 1.0 \
  --spatial-unit unknown
```

## Scientific Notes

- `mag=1-1-1` means native resolution level, not a physical voxel spacing.
- If a bounding box extends outside the dataset bounds, the raw patch is clipped and
  reinserted into the requested output shape with padding. The same clipping and
  reinsertion are applied to the annotation volume so raw data and labels remain
  voxel-aligned.
- `valid_mask` marks which voxels came from real downloaded data versus padding.
- The default NIfTI spatial unit is `unknown` unless you choose otherwise.

## Publishing Notes

- Choose and add a real license before making the repository public.
- Consider tagging the first public release only after one more live end-to-end test on a fresh annotation.

## Development

Run the unit tests with the source tree on `PYTHONPATH`:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

Run lint checks:

```bash
python -m ruff check .
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the recommended development workflow.