from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import numpy as np


def _import_wkw() -> Any:
    import wkw

    return wkw


def load_patch_meta(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def load_nml_root(annotation_dir: Path) -> ET.Element:
    nml_files = sorted((annotation_dir / "extracted").glob("*.nml"))
    if not nml_files:
        raise FileNotFoundError(f"No extracted NML file found under {annotation_dir}")
    return ET.fromstring(nml_files[0].read_text())


def resolve_segment_id(root: ET.Element, box_name: str, segment_id: int | None) -> int:
    if segment_id is not None:
        return segment_id

    segments = root.findall("./volume/segments/segment")
    for segment in segments:
        if segment.attrib.get("name") == box_name:
            return int(segment.attrib["id"])

    target_box = None
    for box in root.findall("./parameters/userBoundingBox"):
        if box.attrib.get("name") == box_name:
            x0 = int(box.attrib["topLeftX"])
            y0 = int(box.attrib["topLeftY"])
            z0 = int(box.attrib["topLeftZ"])
            width = int(box.attrib["width"])
            height = int(box.attrib["height"])
            depth = int(box.attrib["depth"])
            target_box = (x0, y0, z0, x0 + width, y0 + height, z0 + depth)
            break

    if target_box is not None:
        x0, y0, z0, x1, y1, z1 = target_box
        for segment in segments:
            anchor_x = int(segment.attrib["anchorPositionX"])
            anchor_y = int(segment.attrib["anchorPositionY"])
            anchor_z = int(segment.attrib["anchorPositionZ"])
            if x0 <= anchor_x < x1 and y0 <= anchor_y < y1 and z0 <= anchor_z < z1:
                return int(segment.attrib["id"])

    raise ValueError(f"No segment id found for box name {box_name!r}")


def open_volume_dataset(annotation_dir: Path) -> Any:
    wkw = _import_wkw()
    root = annotation_dir / "extracted" / "data_Volume" / "1"
    if not root.exists():
        raise FileNotFoundError(f"Expected extracted WKW dataset at {root}")
    return wkw.Dataset.open(str(root))


def extract_labels(
    annotation_dir: Path,
    patch_meta_path: Path,
    box_name: str,
    output_prefix: Path,
    segment_id: int | None = None,
) -> dict[str, Any]:
    patch_meta = load_patch_meta(patch_meta_path)
    root = load_nml_root(annotation_dir)
    resolved_segment_id = resolve_segment_id(root, box_name, segment_id)
    dataset = open_volume_dataset(annotation_dir)

    requested = patch_meta["bbox"]["requested"]
    clipped = patch_meta["bbox"]["clipped"]
    insert_offset = patch_meta["bbox"]["insert_offset"]

    clipped_top_left = clipped["top_left"]
    clipped_size = clipped["size"]
    clipped_array = dataset.read(clipped_top_left, clipped_size)[0]
    dataset.close()

    labels_full = np.zeros(tuple(requested["size"]), dtype=clipped_array.dtype)
    valid_mask = np.zeros(tuple(requested["size"]), dtype=np.uint8)

    off_x, off_y, off_z = insert_offset
    size_x, size_y, size_z = clipped_array.shape

    labels_full[
        off_x : off_x + size_x,
        off_y : off_y + size_y,
        off_z : off_z + size_z,
    ] = clipped_array
    valid_mask[
        off_x : off_x + size_x,
        off_y : off_y + size_y,
        off_z : off_z + size_z,
    ] = 1

    binary = (labels_full == resolved_segment_id).astype(np.uint8)

    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    labels_path = Path(f"{output_prefix}_labels.npy")
    binary_path = Path(f"{output_prefix}_binary.npy")
    valid_path = Path(f"{output_prefix}_valid_mask.npy")
    meta_path = Path(f"{output_prefix}_labels.meta.json")

    np.save(labels_path, labels_full)
    np.save(binary_path, binary)
    np.save(valid_path, valid_mask)

    metadata = {
        "box_name": box_name,
        "segment_id": resolved_segment_id,
        "requested_bbox": requested,
        "clipped_bbox": clipped,
        "insert_offset": insert_offset,
        "labels_path": str(labels_path),
        "binary_path": str(binary_path),
        "valid_mask_path": str(valid_path),
        "shape": list(labels_full.shape),
        "label_values": sorted(int(value) for value in np.unique(labels_full)),
        "positive_voxels": int(binary.sum()),
        "valid_voxels": int(valid_mask.sum()),
    }
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata