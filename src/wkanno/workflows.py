from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import numpy as np

from wkanno.archive import extract_annotation_archive
from wkanno.client import (
    DEFAULT_BASE_URL,
    ELEMENT_CLASS_TO_DTYPE,
    WebKnossosClient,
    build_annotation_summary,
    compute_overlap,
    read_archive_metadata,
    write_array_output,
)
from wkanno.labels import extract_labels
from wkanno.models import BoundingBox
from wkanno.nifti import export_numpy_inputs
from wkanno.utils import ensure_directory, names_match, slugify, write_json


def resolve_token(token: str | None) -> str:
    resolved = token or os.environ.get("WEBKNOSSOS_TOKEN")
    if not resolved:
        raise ValueError("Missing token. Pass --token or set WEBKNOSSOS_TOKEN.")
    return resolved


def create_client(token: str | None, base_url: str) -> WebKnossosClient:
    return WebKnossosClient(token=resolve_token(token), base_url=base_url)


def inspect_annotation(
    annotation_id: str,
    token: str | None,
    base_url: str,
    download: str,
    volume_format: str,
    output_dir: Path | None,
    extract: bool,
) -> dict[str, Any]:
    client = create_client(token, base_url)
    info = client.get_annotation_info(annotation_id)

    archive_bytes: bytes | None = None
    archive_metadata: dict[str, Any] | None = None
    archive_name: str | None = None

    if download != "none":
        include_volume = download == "full"
        archive_bytes = client.download_annotation_archive(
            annotation_id=annotation_id,
            include_volume=include_volume,
            volume_format=volume_format,
        )
        archive_metadata = read_archive_metadata(archive_bytes)
        suffix = "full" if include_volume else "metadata"
        archive_name = f"{annotation_id}_{suffix}.zip"

    summary = build_annotation_summary(info, archive_metadata)
    if output_dir is not None:
        ensure_directory(output_dir)
        summary_path = output_dir / f"{annotation_id}_summary.json"
        write_json(summary_path, summary)
        if archive_bytes is not None and archive_name is not None:
            archive_path = output_dir / archive_name
            archive_path.write_bytes(archive_bytes)
            if extract:
                extract_annotation_archive(archive_bytes, output_dir)
    return summary


def _anchor_inside_box(segment: dict[str, Any], box: dict[str, Any]) -> bool:
    anchor = segment.get("anchor_position")
    top_left = box.get("top_left")
    size = box.get("size")
    if anchor is None or top_left is None or size is None:
        return False

    x0, y0, z0 = top_left
    width, height, depth = size
    x1 = x0 + width
    y1 = y0 + height
    z1 = z0 + depth
    anchor_x, anchor_y, anchor_z = anchor
    return x0 <= anchor_x < x1 and y0 <= anchor_y < y1 and z0 <= anchor_z < z1


def _match_segment_for_box(
    box: dict[str, Any],
    segments: list[dict[str, Any]],
) -> dict[str, Any] | None:
    name_matches = [
        segment
        for segment in segments
        if names_match(segment.get("name"), box.get("name"))
    ]
    if len(name_matches) == 1:
        return name_matches[0]

    anchor_matches = [segment for segment in segments if _anchor_inside_box(segment, box)]
    if len(anchor_matches) == 1:
        return anchor_matches[0]
    return None


def summarize_annotation_boxes(summary: dict[str, Any]) -> dict[str, Any]:
    nml = summary.get("archive", {}).get("nml", {})
    boxes = nml.get("user_bounding_boxes", [])
    segments = nml.get("segments", [])

    box_entries = []
    for box in boxes:
        matched_segment = _match_segment_for_box(box, segments)
        box_entries.append(
            {
                "id": box.get("id"),
                "name": box.get("name"),
                "top_left": box.get("top_left"),
                "size": box.get("size"),
                "segment_id": None if matched_segment is None else matched_segment.get("id"),
                "segment_name": None if matched_segment is None else matched_segment.get("name"),
                "segment_anchor_position": None
                if matched_segment is None
                else matched_segment.get("anchor_position"),
            }
        )

    return {
        "annotation_id": summary.get("annotation_id"),
        "annotation_name": summary.get("name"),
        "dataset_name": summary.get("dataset_name"),
        "dataset_id": summary.get("dataset_id"),
        "box_count": len(box_entries),
        "boxes": box_entries,
    }


def list_annotation_boxes(
    annotation_id: str,
    token: str | None,
    base_url: str,
    output_dir: Path | None,
) -> dict[str, Any]:
    summary = inspect_annotation(
        annotation_id=annotation_id,
        token=token,
        base_url=base_url,
        download="metadata",
        volume_format="wkw",
        output_dir=output_dir,
        extract=False,
    )
    return summarize_annotation_boxes(summary)


def _load_box_from_summary(summary_path: Path, box_name: str) -> tuple[dict[str, Any], BoundingBox]:
    summary = json.loads(summary_path.read_text())
    boxes = summary["archive"]["nml"]["user_bounding_boxes"]
    matches = [box for box in boxes if names_match(box.get("name"), box_name)]
    if not matches:
        raise ValueError(f"No user bounding box named {box_name!r} found in annotation summary")
    if len(matches) > 1:
        matched_names = sorted({str(box.get("name", "")) for box in matches})
        raise ValueError(f"Multiple user bounding boxes matched {box_name!r}: {matched_names}")
    match = matches[0]
    bbox = BoundingBox.from_lists(match["top_left"], match["size"])
    return summary, bbox


def download_raw_patch_from_summary(
    annotation_summary: Path,
    box_name: str,
    output_path: Path,
    token: str | None,
    base_url: str,
    layer: str,
    mag: str,
    padding_value: float,
) -> dict[str, Any]:
    summary, requested_bbox = _load_box_from_summary(annotation_summary, box_name)
    client = create_client(token, base_url)
    dataset_info = client.get_dataset_info(summary["dataset_id"])
    layers = dataset_info["dataSource"]["dataLayers"]
    matches = [item for item in layers if item["name"] == layer]
    if not matches:
        raise ValueError(f"Layer {layer!r} not found in dataset metadata")
    layer_info = matches[0]

    dtype = np.dtype(ELEMENT_CLASS_TO_DTYPE[layer_info["elementClass"]])
    overlap = compute_overlap(requested_bbox, layer_info["boundingBox"])
    sharing_token = client.get_sharing_token(summary["dataset_id"])
    clipped_patch = client.download_raw_patch(
        organization=summary["organization"],
        dataset_name=summary["dataset_name"],
        layer=layer,
        mag=mag,
        sharing_token=sharing_token,
        clipped_box=overlap.clipped,
        dtype=dtype,
    )

    req_w, req_h, req_d = overlap.requested.size
    patch = np.full((req_w, req_h, req_d), padding_value, dtype=dtype)
    off_x, off_y, off_z = overlap.insert_offset
    clip_w, clip_h, clip_d = overlap.clipped.size
    patch[
        off_x : off_x + clip_w,
        off_y : off_y + clip_h,
        off_z : off_z + clip_d,
    ] = clipped_patch

    metadata = {
        "source": {
            "url": base_url,
            "dataset_id": summary["dataset_id"],
            "dataset_name": summary["dataset_name"],
            "organization": summary["organization"],
            "layer": layer,
            "mag": mag,
        },
        "bbox": overlap.to_dict(),
        "dtype": str(dtype),
        "shape": list(patch.shape),
        "padding_value": padding_value,
    }
    write_array_output(output_path, patch, metadata)
    return metadata


def export_nifti_products(
    inputs: list[Path],
    output_dir: Path,
    voxel_size: float,
    spatial_unit: str,
) -> list[Path]:
    return export_numpy_inputs(inputs, output_dir, voxel_size, spatial_unit)


def fetch_box(
    annotation_id: str,
    box_name: str,
    output_dir: Path,
    token: str | None,
    base_url: str = DEFAULT_BASE_URL,
    layer: str = "0",
    mag: str = "1-1-1",
    padding_value: float = 0.0,
    export_nifti: bool = False,
    voxel_size: float = 1.0,
    spatial_unit: str = "unknown",
) -> dict[str, Any]:
    ensure_directory(output_dir)

    annotation_dir = ensure_directory(output_dir / f"annotation_{annotation_id}")
    summary = inspect_annotation(
        annotation_id=annotation_id,
        token=token,
        base_url=base_url,
        download="full",
        volume_format="wkw",
        output_dir=annotation_dir,
        extract=True,
    )
    summary_path = annotation_dir / f"{annotation_id}_summary.json"

    annotation_name = summary.get("name") or summary.get("dataset_name") or annotation_id
    base_name = slugify(f"{annotation_name}_{box_name}")
    raw_path = output_dir / f"{base_name}.npy"
    raw_meta = download_raw_patch_from_summary(
        annotation_summary=summary_path,
        box_name=box_name,
        output_path=raw_path,
        token=token,
        base_url=base_url,
        layer=layer,
        mag=mag,
        padding_value=padding_value,
    )

    labels_meta = extract_labels(
        annotation_dir=annotation_dir,
        patch_meta_path=Path(str(raw_path) + ".meta.json"),
        box_name=box_name,
        output_prefix=output_dir / base_name,
    )

    nifti_paths: list[str] = []
    if export_nifti:
        nifti_dir = ensure_directory(output_dir / "nifti")
        written = export_nifti_products(
            inputs=[
                raw_path,
                Path(labels_meta["labels_path"]),
                Path(labels_meta["binary_path"]),
                Path(labels_meta["valid_mask_path"]),
            ],
            output_dir=nifti_dir,
            voxel_size=voxel_size,
            spatial_unit=spatial_unit,
        )
        nifti_paths = [str(path) for path in written]

    manifest = {
        "annotation_id": annotation_id,
        "box_name": box_name,
        "summary_path": str(summary_path),
        "raw_path": str(raw_path),
        "raw_meta_path": str(Path(str(raw_path) + ".meta.json")),
        "labels_meta_path": str(output_dir / f"{base_name}_labels.meta.json"),
        "nifti_paths": nifti_paths,
        "dataset": raw_meta["source"],
    }
    manifest_path = output_dir / f"{base_name}_manifest.json"
    write_json(manifest_path, manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest