import json
import tempfile
import unittest
from pathlib import Path

from wkanno.workflows import _load_box_from_summary, summarize_annotation_boxes


LIVE_SUMMARY = {
    "annotation_id": "6982650e010000a3019f7143",
    "name": "macaque_PV",
    "dataset_name": "000010_macaque_PV.ome.zarr",
    "dataset_id": "690121b6010000de00be951e",
    "archive": {
        "nml": {
            "user_bounding_boxes": [
                {
                    "id": "12",
                    "name": "White-Gray Transition",
                    "top_left": [0, 741, 2923],
                    "size": [100, 250, 250],
                },
                {
                    "id": "14",
                    "name": "WM 1",
                    "top_left": [0, 1639, 1443],
                    "size": [120, 250, 250],
                },
                {
                    "id": "15",
                    "name": "WM 2",
                    "top_left": [5, 2301, 1503],
                    "size": [120, 250, 250],
                },
                {
                    "id": "1",
                    "name": "GM 1",
                    "top_left": [0, 1672, 5077],
                    "size": [100, 250, 250],
                },
            ],
            "segments": [
                {
                    "id": "3",
                    "name": "Annotations transition",
                    "anchor_position": [99, 863, 3109],
                },
                {
                    "id": "16",
                    "name": "Annotations WM 1",
                    "anchor_position": [105, 1819, 1651],
                },
                {
                    "id": "17",
                    "name": "Annotations WM 2",
                    "anchor_position": [133, 1892, 1761],
                },
                {
                    "id": "2",
                    "name": "Annotations GM 1",
                    "anchor_position": [100, 1766, 5287],
                },
            ],
        }
    },
}


class SummarizeAnnotationBoxesTests(unittest.TestCase):
    def test_summary_includes_box_to_segment_matches(self) -> None:
        listing = summarize_annotation_boxes(LIVE_SUMMARY)

        self.assertEqual(listing["box_count"], 4)
        self.assertEqual(listing["boxes"][0]["name"], "White-Gray Transition")
        self.assertEqual(listing["boxes"][0]["segment_id"], "3")
        self.assertEqual(listing["boxes"][1]["name"], "WM 1")
        self.assertEqual(listing["boxes"][1]["segment_id"], "16")
        self.assertEqual(listing["boxes"][2]["name"], "WM 2")
        self.assertEqual(listing["boxes"][2]["segment_id"], "17")
        self.assertEqual(listing["boxes"][3]["name"], "GM 1")
        self.assertEqual(listing["boxes"][3]["segment_id"], "2")

    def test_load_box_from_summary_normalizes_name_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            summary_path = Path(tmpdir) / "summary.json"
            summary_path.write_text(json.dumps(LIVE_SUMMARY))

            _, bbox = _load_box_from_summary(summary_path, "‘gm 1’")

        self.assertEqual(bbox.top_left, (0, 1672, 5077))
        self.assertEqual(bbox.size, (100, 250, 250))


if __name__ == "__main__":
    unittest.main()