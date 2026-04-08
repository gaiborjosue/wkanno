import unittest

from wkanno.client import compute_overlap
from wkanno.models import BoundingBox


class ComputeOverlapTests(unittest.TestCase):
    def test_overlap_with_negative_origin_and_padding(self) -> None:
        requested = BoundingBox(top_left=(-2, 919, 2645), size=(114, 250, 250))
        dataset_box = {
            "topLeft": [0, 0, 0],
            "width": 10000,
            "height": 10000,
            "depth": 10000,
        }

        overlap = compute_overlap(requested, dataset_box)

        self.assertEqual(overlap.requested.top_left, (-2, 919, 2645))
        self.assertEqual(overlap.clipped.top_left, (0, 919, 2645))
        self.assertEqual(overlap.clipped.size, (112, 250, 250))
        self.assertEqual(overlap.insert_offset, (2, 0, 0))

    def test_overlap_matches_wm_case_shape(self) -> None:
        requested = BoundingBox(top_left=(-2, 919, 2645), size=(114, 250, 250))
        dataset_box = {
            "topLeft": [0, 919, 2645],
            "width": 111,
            "height": 250,
            "depth": 250,
        }

        overlap = compute_overlap(requested, dataset_box)

        self.assertEqual(overlap.clipped.top_left, (0, 919, 2645))
        self.assertEqual(overlap.clipped.size, (111, 250, 250))
        self.assertEqual(overlap.insert_offset, (2, 0, 0))


if __name__ == "__main__":
    unittest.main()