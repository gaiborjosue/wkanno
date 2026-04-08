from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BoundingBox:
    top_left: tuple[int, int, int]
    size: tuple[int, int, int]

    @classmethod
    def from_lists(cls, top_left: list[int], size: list[int]) -> "BoundingBox":
        return cls(tuple(top_left), tuple(size))

    def to_dict(self) -> dict[str, list[int]]:
        return {
            "top_left": list(self.top_left),
            "size": list(self.size),
        }

    def to_bbox_tuple(self) -> tuple[int, int, int, int, int, int]:
        return (*self.top_left, *self.size)


@dataclass(frozen=True)
class UserBoundingBox:
    id: str | None
    name: str | None
    bbox: BoundingBox

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            **self.bbox.to_dict(),
        }


@dataclass(frozen=True)
class Segment:
    id: str | None
    name: str | None
    anchor_position: tuple[int, int, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "anchor_position": list(self.anchor_position),
        }


@dataclass(frozen=True)
class ParsedNML:
    experiment: dict[str, str] | None
    scale: dict[str, str] | None
    edit_position: dict[str, str] | None
    zoom_level: dict[str, str] | None
    user_bounding_boxes: list[UserBoundingBox]
    segments: list[Segment]

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment": self.experiment,
            "scale": self.scale,
            "edit_position": self.edit_position,
            "zoom_level": self.zoom_level,
            "user_bounding_boxes": [box.to_dict() for box in self.user_bounding_boxes],
            "segments": [segment.to_dict() for segment in self.segments],
        }

    def find_box(self, name: str) -> UserBoundingBox:
        matches = [box for box in self.user_bounding_boxes if box.name == name]
        if not matches:
            raise ValueError(f"No user bounding box named {name!r} found in annotation metadata")
        return matches[0]

    def find_segment(self, name: str) -> Segment:
        matches = [segment for segment in self.segments if segment.name == name]
        if not matches:
            raise ValueError(f"No segment named {name!r} found in annotation metadata")
        return matches[0]


@dataclass(frozen=True)
class Overlap:
    requested: BoundingBox
    clipped: BoundingBox
    insert_offset: tuple[int, int, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "requested": self.requested.to_dict(),
            "clipped": self.clipped.to_dict(),
            "insert_offset": list(self.insert_offset),
        }