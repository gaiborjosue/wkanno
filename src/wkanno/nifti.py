from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np


def save_nifti(
    array: np.ndarray,
    output_path: Path,
    voxel_size: float,
    spatial_unit: str,
) -> None:
    affine = np.diag([voxel_size, voxel_size, voxel_size, 1.0])
    image = nib.Nifti1Image(array, affine=affine)
    image.header.set_xyzt_units(xyz=spatial_unit)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(image, str(output_path))


def export_numpy_inputs(
    input_paths: list[Path],
    output_dir: Path,
    voxel_size: float,
    spatial_unit: str,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for input_path in input_paths:
        array = np.load(input_path)
        output_path = output_dir / f"{input_path.stem}.nii"
        save_nifti(array, output_path, voxel_size, spatial_unit)
        written.append(output_path)
    return written