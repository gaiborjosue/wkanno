from __future__ import annotations

import io
import zipfile
from pathlib import Path

from wkanno.utils import ensure_directory


def extract_annotation_archive(archive_bytes: bytes, output_dir: Path) -> Path:
    extracted_dir = ensure_directory(output_dir / "extracted")
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as outer_zip:
        outer_zip.extractall(extracted_dir)
        if "data_Volume.zip" in outer_zip.namelist():
            with zipfile.ZipFile(io.BytesIO(outer_zip.read("data_Volume.zip"))) as inner_zip:
                inner_zip.extractall(extracted_dir / "data_Volume")
    return extracted_dir


def extract_annotation_archive_from_path(archive_path: Path, output_dir: Path) -> Path:
    return extract_annotation_archive(archive_path.read_bytes(), output_dir)