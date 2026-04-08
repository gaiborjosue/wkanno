import unittest

from wkanno.workflows import summarize_annotation_boxes


PV_SUMMARY = {
    "annotation_id": "6982650e010000a3019f7143",
    "name": "macaque_PV",
    "dataset_name": "000010_macaque_PV.ome.zarr",
    "dataset_id": "690121b6010000de00be951e",
    "archive": {
        "nml": {
            "user_bounding_boxes": [
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
            ],
            "segments": [
                {
                    "id": "16",
                    "name": "Annotations WM 1",
                    "anchor_position": [105, 1819, 1651],
                },
                {
                    "id": "17",
                    "name": "Annotations WM 2",
                    "anchor_position": [35, 2500, 1629],
                },
            ],
        }
    },
}


class SummarizeAnnotationBoxesTests(unittest.TestCase):
    def test_summary_includes_box_to_segment_matches(self) -> None:
        listing = summarize_annotation_boxes(PV_SUMMARY)

        self.assertEqual(listing["box_count"], 2)
        self.assertEqual(listing["boxes"][0]["name"], "WM 1")
        self.assertEqual(listing["boxes"][0]["segment_id"], "16")
        self.assertEqual(listing["boxes"][1]["name"], "WM 2")
        self.assertEqual(listing["boxes"][1]["segment_id"], "17")


if __name__ == "__main__":
    unittest.main()