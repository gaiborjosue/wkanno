# wkanno

`wkanno` is a Python CLI for downloading WebKnossos annotation metadata, aligned raw patches, label volumes, binary masks, and valid masks.

It uses the direct WebKnossos REST flow that works against older server API versions.

## Install

```bash
python3 -m pip install --user pipx
~/.local/bin/pipx ensurepath
```

Open a new shell, or run:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Then install `wkanno` from GitHub:

```bash
pipx install git+https://github.com/gaiborjosue/wkanno.git
```

## Authenticate

Get it from: https://webknossos.lincbrain.org/auth/token

```bash
export WEBKNOSSOS_TOKEN=your_token_here
```

## Quick Start

List the available boxes in an annotation:

```bash
wkanno list-boxes 6982650e010000a3019f7143
```

Fetch one box by name:

```bash
wkanno fetch-box 6982650e010000a3019f7143 'WM 2' \
  --output-dir ./wkanno_out \
  --export-nifti
```

## Main Commands

Inspect an annotation:

```bash
wkanno inspect 6982650e010000a3019f7143 --download metadata --output-dir ./inspect_out
```

Fetch a full box workflow:

```bash
wkanno fetch-box 6982650e010000a3019f7143 'White-Gray Transition' \
  --output-dir ./wkanno_out \
  --export-nifti
```

Download only the raw patch from an existing summary:

```bash
wkanno download-raw \
  --annotation-summary ./inspect_out/6982650e010000a3019f7143_summary.json \
  --box-name 'WM 1' \
  --output ./macaque_PV_WM_1.npy
```

Extract only labels from an extracted annotation bundle:

```bash
wkanno extract-labels \
  --annotation-dir ./annotation_6982650e010000a3019f7143 \
  --patch-meta ./macaque_PV_WM_1.npy.meta.json \
  --box-name 'WM 1' \
  --output-prefix ./macaque_PV_WM_1
```

Export `.npy` arrays to NIfTI:

```bash
wkanno export-nifti \
  --inputs ./macaque_PV_WM_1.npy ./macaque_PV_WM_1_binary.npy \
  --output-dir ./nifti \
  --voxel-size 1.0 \
  --spatial-unit unknown
```

## Notes

- `mag=1-1-1` means native resolution level, not a physical voxel spacing.
- If a box extends outside dataset bounds, `wkanno` clips the download and pads it back into the requested shape.
- The same clipping and reinsertion are applied to the annotation volume so raw data and labels stay voxel-aligned.
- `valid_mask` marks voxels that came from real downloaded data rather than padding.
- NIfTI spatial units default to `unknown` unless you set them explicitly.

## Development

Install locally for development:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Run tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

Run lint checks:

```bash
python -m ruff check .
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the recommended development workflow.
