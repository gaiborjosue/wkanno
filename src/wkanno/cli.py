from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from wkanno import __version__
from wkanno.archive import extract_annotation_archive_from_path
from wkanno.labels import extract_labels
from wkanno.nifti import export_numpy_inputs
from wkanno.workflows import (
    DEFAULT_BASE_URL,
    download_raw_patch_from_summary,
    fetch_box,
    inspect_annotation,
    list_annotation_boxes,
)


def _render_box_listing(listing: dict[str, object]) -> str:
    lines = [
        f"Annotation: {listing['annotation_id']} ({listing['annotation_name']})",
        f"Dataset: {listing['dataset_name']} [{listing['dataset_id']}]",
        f"Boxes: {listing['box_count']}",
    ]
    boxes = listing.get("boxes", [])
    if not boxes:
        lines.append("No user bounding boxes found.")
        return "\n".join(lines)

    for box in boxes:
        segment_suffix = ""
        if box["segment_id"] is not None:
            segment_suffix = (
                f" | segment={box['segment_id']}"
                f" ({box['segment_name']})"
            )
        lines.append(
            f"- {box['name']} | id={box['id']} | top_left={box['top_left']} "
            f"| size={box['size']}{segment_suffix}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wkanno",
        description="Download WebKnossos annotations, aligned raw patches, and label products.",
    )
    parser.add_argument("--version", action="version", version=f"wkanno {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect an annotation and optionally download its archive",
    )
    inspect_parser.add_argument("annotation_id")
    inspect_parser.add_argument("--token", default=None)
    inspect_parser.add_argument("--url", default=DEFAULT_BASE_URL)
    inspect_parser.add_argument(
        "--download",
        choices=["none", "metadata", "full"],
        default="metadata",
    )
    inspect_parser.add_argument("--volume-format", choices=["wkw", "zarr3"], default="wkw")
    inspect_parser.add_argument("--output-dir", type=Path, default=None)
    inspect_parser.add_argument("--extract", action="store_true")

    list_parser = subparsers.add_parser(
        "list-boxes",
        help="List the named user bounding boxes inside an annotation",
    )
    list_parser.add_argument("annotation_id")
    list_parser.add_argument("--token", default=None)
    list_parser.add_argument("--url", default=DEFAULT_BASE_URL)
    list_parser.add_argument("--output-dir", type=Path, default=None)
    list_parser.add_argument("--json", action="store_true")

    raw_parser = subparsers.add_parser(
        "download-raw",
        help="Download a raw patch for a named user box",
    )
    raw_parser.add_argument("--annotation-summary", type=Path, required=True)
    raw_parser.add_argument("--box-name", required=True)
    raw_parser.add_argument("--output", type=Path, required=True)
    raw_parser.add_argument("--token", default=None)
    raw_parser.add_argument("--url", default=DEFAULT_BASE_URL)
    raw_parser.add_argument("--layer", default="0")
    raw_parser.add_argument("--mag", default="1-1-1")
    raw_parser.add_argument("--padding-value", type=float, default=0.0)

    labels_parser = subparsers.add_parser(
        "extract-labels",
        help="Extract aligned label arrays from an extracted annotation bundle",
    )
    labels_parser.add_argument("--annotation-dir", type=Path, required=True)
    labels_parser.add_argument("--patch-meta", type=Path, required=True)
    labels_parser.add_argument("--box-name", required=True)
    labels_parser.add_argument("--segment-id", type=int, default=None)
    labels_parser.add_argument("--output-prefix", type=Path, required=True)

    export_parser = subparsers.add_parser("export-nifti", help="Export .npy arrays to NIfTI")
    export_parser.add_argument("--inputs", type=Path, nargs="+", required=True)
    export_parser.add_argument("--output-dir", type=Path, required=True)
    export_parser.add_argument("--voxel-size", type=float, default=1.0)
    export_parser.add_argument(
        "--spatial-unit",
        choices=["unknown", "meter", "mm", "micron"],
        default="unknown",
    )

    extract_parser = subparsers.add_parser(
        "extract-archive",
        help="Extract a downloaded annotation archive in place",
    )
    extract_parser.add_argument("--archive", type=Path, required=True)
    extract_parser.add_argument("--output-dir", type=Path, required=True)

    fetch_parser = subparsers.add_parser(
        "fetch-box",
        help="Run the full workflow for a named annotation box",
    )
    fetch_parser.add_argument("annotation_id")
    fetch_parser.add_argument("box_name")
    fetch_parser.add_argument("--output-dir", type=Path, required=True)
    fetch_parser.add_argument("--token", default=None)
    fetch_parser.add_argument("--url", default=DEFAULT_BASE_URL)
    fetch_parser.add_argument("--layer", default="0")
    fetch_parser.add_argument("--mag", default="1-1-1")
    fetch_parser.add_argument("--padding-value", type=float, default=0.0)
    fetch_parser.add_argument("--export-nifti", action="store_true")
    fetch_parser.add_argument("--voxel-size", type=float, default=1.0)
    fetch_parser.add_argument(
        "--spatial-unit",
        choices=["unknown", "meter", "mm", "micron"],
        default="unknown",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "inspect":
            summary = inspect_annotation(
                annotation_id=args.annotation_id,
                token=args.token,
                base_url=args.url,
                download=args.download,
                volume_format=args.volume_format,
                output_dir=args.output_dir,
                extract=args.extract,
            )
            print(json.dumps(summary, indent=2))
            return 0

        if args.command == "list-boxes":
            listing = list_annotation_boxes(
                annotation_id=args.annotation_id,
                token=args.token,
                base_url=args.url,
                output_dir=args.output_dir,
            )
            if args.json:
                print(json.dumps(listing, indent=2))
            else:
                print(_render_box_listing(listing))
            return 0

        if args.command == "download-raw":
            metadata = download_raw_patch_from_summary(
                annotation_summary=args.annotation_summary,
                box_name=args.box_name,
                output_path=args.output,
                token=args.token,
                base_url=args.url,
                layer=args.layer,
                mag=args.mag,
                padding_value=args.padding_value,
            )
            print(json.dumps(metadata, indent=2))
            return 0

        if args.command == "extract-labels":
            metadata = extract_labels(
                annotation_dir=args.annotation_dir,
                patch_meta_path=args.patch_meta,
                box_name=args.box_name,
                output_prefix=args.output_prefix,
                segment_id=args.segment_id,
            )
            print(json.dumps(metadata, indent=2))
            return 0

        if args.command == "export-nifti":
            written = export_numpy_inputs(
                input_paths=args.inputs,
                output_dir=args.output_dir,
                voxel_size=args.voxel_size,
                spatial_unit=args.spatial_unit,
            )
            print(json.dumps({"written": [str(path) for path in written]}, indent=2))
            return 0

        if args.command == "extract-archive":
            extracted_dir = extract_annotation_archive_from_path(args.archive, args.output_dir)
            print(json.dumps({"extracted_dir": str(extracted_dir)}, indent=2))
            return 0

        if args.command == "fetch-box":
            manifest = fetch_box(
                annotation_id=args.annotation_id,
                box_name=args.box_name,
                output_dir=args.output_dir,
                token=args.token,
                base_url=args.url,
                layer=args.layer,
                mag=args.mag,
                padding_value=args.padding_value,
                export_nifti=args.export_nifti,
                voxel_size=args.voxel_size,
                spatial_unit=args.spatial_unit,
            )
            print(json.dumps(manifest, indent=2))
            return 0

        parser.error(f"Unknown command: {args.command}")
        return 2
    except Exception as exc:  # pragma: no cover - CLI boundary
        print(f"wkanno error: {exc}", file=sys.stderr)
        return 1