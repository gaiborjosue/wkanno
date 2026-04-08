from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import quote

import numpy as np
import requests

from wkanno.models import BoundingBox, Overlap
from wkanno.nml import parse_nml_text

API_VERSION = 9
DEFAULT_BASE_URL = "https://webknossos.lincbrain.org"

ELEMENT_CLASS_TO_DTYPE = {
    "uint8": np.uint8,
    "uint16": np.uint16,
    "uint32": np.uint32,
    "uint64": np.uint64,
    "int8": np.int8,
    "int16": np.int16,
    "int32": np.int32,
    "int64": np.int64,
    "float32": np.float32,
    "float64": np.float64,
}


class WebKnossosClient:
    def __init__(self, token: str, base_url: str = DEFAULT_BASE_URL, api_version: int = API_VERSION):
        self.base_url = base_url.rstrip("/")
        self.api_version = api_version
        self.session = requests.Session()
        self.session.headers.update({"X-Auth-Token": token})

    def get_annotation_info(self, annotation_id: str) -> dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}/api/v{self.api_version}/annotations/{annotation_id}/info",
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def download_annotation_archive(
        self,
        annotation_id: str,
        include_volume: bool,
        volume_format: str,
    ) -> bytes:
        response = self.session.get(
            f"{self.base_url}/api/v{self.api_version}/annotations/{annotation_id}/download",
            params={
                "skipVolumeData": str(not include_volume).lower(),
                "volumeDataZipFormat": volume_format,
            },
            timeout=300,
        )
        response.raise_for_status()
        return response.content

    def get_dataset_info(self, dataset_id: str) -> dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}/api/v{self.api_version}/datasets/{dataset_id}",
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def get_sharing_token(self, dataset_id: str) -> str:
        response = self.session.get(
            f"{self.base_url}/api/v{self.api_version}/datasets/{dataset_id}/sharingToken",
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["sharingToken"]

    def download_raw_patch(
        self,
        organization: str,
        dataset_name: str,
        layer: str,
        mag: str,
        sharing_token: str,
        clipped_box: BoundingBox,
        dtype: np.dtype[Any],
    ) -> np.ndarray:
        x, y, z = clipped_box.top_left
        width, height, depth = clipped_box.size
        dataset_name_encoded = quote(dataset_name, safe="")
        response = self.session.get(
            f"{self.base_url}/data/datasets/{organization}/{dataset_name_encoded}/layers/{layer}/data",
            params={
                "mag": mag,
                "x": x,
                "y": y,
                "z": z,
                "width": width,
                "height": height,
                "depth": depth,
                "token": sharing_token,
            },
            timeout=300,
        )
        response.raise_for_status()

        missing = response.headers.get("MISSING-BUCKETS")
        if missing not in (None, "[]"):
            raise RuntimeError(f"Datastore response reported missing buckets: {missing}")

        return np.frombuffer(response.content, dtype=dtype).reshape(
            (1, width, height, depth), order="F"
        )[0]


def read_archive_metadata(archive_bytes: bytes) -> dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as outer_zip:
        names = outer_zip.namelist()
        nml_name = next((name for name in names if name.endswith(".nml")), None)
        if nml_name is None:
            return {"archive_entries": names}

        nml_text = outer_zip.read(nml_name).decode("utf-8", errors="replace")
        metadata: dict[str, Any] = {
            "archive_entries": names,
            "nml_name": nml_name,
            "nml": parse_nml_text(nml_text).to_dict(),
        }

        if "data_Volume.zip" in names:
            with zipfile.ZipFile(io.BytesIO(outer_zip.read("data_Volume.zip"))) as inner_zip:
                inner_names = inner_zip.namelist()
            metadata["volume_archive_entries_preview"] = inner_names[:200]
            metadata["volume_archive_entry_count"] = len(inner_names)

        return metadata


def build_annotation_summary(
    info: dict[str, Any],
    archive_metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    summary = {
        "annotation_id": info.get("id"),
        "name": info.get("name"),
        "organization": info.get("organization"),
        "dataset_name": info.get("dataSetName"),
        "dataset_id": info.get("datasetId"),
        "annotation_layers": info.get("annotationLayers", []),
        "restrictions": info.get("restrictions", {}),
        "visibility": info.get("visibility"),
    }
    if archive_metadata is not None:
        summary["archive"] = archive_metadata
    return summary


def compute_overlap(requested: BoundingBox, dataset_box: dict[str, Any]) -> Overlap:
    req_x, req_y, req_z = requested.top_left
    req_w, req_h, req_d = requested.size
    req_x1 = req_x + req_w
    req_y1 = req_y + req_h
    req_z1 = req_z + req_d

    data_x, data_y, data_z = dataset_box["topLeft"]
    data_w = dataset_box["width"]
    data_h = dataset_box["height"]
    data_d = dataset_box["depth"]
    data_x1 = data_x + data_w
    data_y1 = data_y + data_h
    data_z1 = data_z + data_d

    clip_x0 = max(req_x, data_x)
    clip_y0 = max(req_y, data_y)
    clip_z0 = max(req_z, data_z)
    clip_x1 = min(req_x1, data_x1)
    clip_y1 = min(req_y1, data_y1)
    clip_z1 = min(req_z1, data_z1)

    if clip_x0 >= clip_x1 or clip_y0 >= clip_y1 or clip_z0 >= clip_z1:
        raise ValueError("Requested bounding box does not overlap the dataset bounds")

    return Overlap(
        requested=requested,
        clipped=BoundingBox(
            top_left=(clip_x0, clip_y0, clip_z0),
            size=(clip_x1 - clip_x0, clip_y1 - clip_y0, clip_z1 - clip_z0),
        ),
        insert_offset=(clip_x0 - req_x, clip_y0 - req_y, clip_z0 - req_z),
    )


def write_array_output(output_path: Path, array: np.ndarray, metadata: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix == ".npy":
        np.save(output_path, array)
    else:
        memmap = np.memmap(str(output_path), dtype=array.dtype, mode="w+", shape=array.shape)
        memmap[...] = array
        memmap.flush()
        del memmap
        Path(str(output_path) + ".json").write_text(
            json.dumps({"shape": list(array.shape), "dtype": str(array.dtype)}) + "\n"
        )

    Path(str(output_path) + ".meta.json").write_text(json.dumps(metadata, indent=2) + "\n")