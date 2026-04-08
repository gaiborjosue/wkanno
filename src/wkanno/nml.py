from __future__ import annotations

import xml.etree.ElementTree as ET

from wkanno.models import BoundingBox, ParsedNML, Segment, UserBoundingBox


def parse_nml_text(nml_text: str) -> ParsedNML:
    root = ET.fromstring(nml_text)
    params = root.find("parameters")
    if params is None:
        return ParsedNML(None, None, None, None, [], [])

    experiment = params.find("experiment")
    scale = params.find("scale")
    edit_position = params.find("editPosition")
    zoom = params.find("zoomLevel")

    user_boxes: list[UserBoundingBox] = []
    for box in params.findall("userBoundingBox"):
        user_boxes.append(
            UserBoundingBox(
                id=box.attrib.get("id"),
                name=box.attrib.get("name"),
                bbox=BoundingBox(
                    top_left=(
                        int(box.attrib["topLeftX"]),
                        int(box.attrib["topLeftY"]),
                        int(box.attrib["topLeftZ"]),
                    ),
                    size=(
                        int(box.attrib["width"]),
                        int(box.attrib["height"]),
                        int(box.attrib["depth"]),
                    ),
                ),
            )
        )

    segments: list[Segment] = []
    for segment in root.findall("./volume/segments/segment"):
        segments.append(
            Segment(
                id=segment.attrib.get("id"),
                name=segment.attrib.get("name"),
                anchor_position=(
                    int(segment.attrib["anchorPositionX"]),
                    int(segment.attrib["anchorPositionY"]),
                    int(segment.attrib["anchorPositionZ"]),
                ),
            )
        )

    return ParsedNML(
        experiment=dict(experiment.attrib) if experiment is not None else None,
        scale=dict(scale.attrib) if scale is not None else None,
        edit_position=dict(edit_position.attrib) if edit_position is not None else None,
        zoom_level=dict(zoom.attrib) if zoom is not None else None,
        user_bounding_boxes=user_boxes,
        segments=segments,
    )