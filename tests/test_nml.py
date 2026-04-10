import unittest

from wkanno.nml import parse_nml_text

SAMPLE_NML = """
<things>
  <parameters>
    <experiment name="dataset" organization="LINC" datasetId="abc" />
    <scale x="1.0" y="1.0" z="1.0" unit="nanometer" />
    <editPosition x="0" y="1" z="2" />
    <zoomLevel zoom="0.5" />
    <userBoundingBox
      id="4"
      name="WM"
      topLeftX="-2"
      topLeftY="919"
      topLeftZ="2645"
      width="114"
      height="250"
      depth="250"
    />
  </parameters>
  <volume>
    <segments>
      <segment
        id="10"
        name="WM"
        anchorPositionX="42"
        anchorPositionY="1144"
        anchorPositionZ="2811"
      />
    </segments>
  </volume>
</things>
"""


class ParseNMLTests(unittest.TestCase):
    def test_parse_nml_extracts_boxes_and_segments(self) -> None:
        parsed = parse_nml_text(SAMPLE_NML)

        self.assertEqual(parsed.scale, {"x": "1.0", "y": "1.0", "z": "1.0", "unit": "nanometer"})
        self.assertEqual(len(parsed.user_bounding_boxes), 1)
        self.assertEqual(parsed.user_bounding_boxes[0].name, "WM")
        self.assertEqual(parsed.user_bounding_boxes[0].bbox.top_left, (-2, 919, 2645))
        self.assertEqual(parsed.user_bounding_boxes[0].bbox.size, (114, 250, 250))
        self.assertEqual(len(parsed.segments), 1)
        self.assertEqual(parsed.segments[0].name, "WM")
        self.assertEqual(parsed.segments[0].anchor_position, (42, 1144, 2811))


if __name__ == "__main__":
    unittest.main()