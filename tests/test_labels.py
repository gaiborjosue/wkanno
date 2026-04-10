import unittest
import xml.etree.ElementTree as ET

from wkanno.labels import resolve_segment_id


LIVE_STYLE_XML = """
<things>
  <parameters>
    <userBoundingBox id="12" name="White-Gray Transition" topLeftX="0" topLeftY="741" topLeftZ="2923" width="100" height="250" depth="250" />
    <userBoundingBox id="14" name="WM 1" topLeftX="0" topLeftY="1639" topLeftZ="1443" width="120" height="250" depth="250" />
    <userBoundingBox id="15" name="WM 2" topLeftX="5" topLeftY="2301" topLeftZ="1503" width="120" height="250" depth="250" />
    <userBoundingBox id="1" name="GM 1" topLeftX="0" topLeftY="1672" topLeftZ="5077" width="100" height="250" depth="250" />
  </parameters>
  <volume>
    <segments>
      <segment id="3" name="Annotations transition" anchorPositionX="99" anchorPositionY="863" anchorPositionZ="3109" />
      <segment id="16" name="Annotations WM 1" anchorPositionX="105" anchorPositionY="1819" anchorPositionZ="1651" />
      <segment id="17" name="Annotations WM 2" anchorPositionX="133" anchorPositionY="1892" anchorPositionZ="1761" />
      <segment id="2" name="Annotations GM 1" anchorPositionX="100" anchorPositionY="1766" anchorPositionZ="5287" />
    </segments>
  </volume>
</things>
"""


class ResolveSegmentIdTests(unittest.TestCase):
    def test_falls_back_to_anchor_inside_box(self) -> None:
        root = ET.fromstring(LIVE_STYLE_XML)
        self.assertEqual(resolve_segment_id(root, "White-Gray Transition", None), 3)

    def test_matches_segment_names_with_annotations_prefix(self) -> None:
        root = ET.fromstring(LIVE_STYLE_XML)
        self.assertEqual(resolve_segment_id(root, "WM 1", None), 16)
        self.assertEqual(resolve_segment_id(root, "WM 2", None), 17)

    def test_normalizes_user_supplied_box_name(self) -> None:
        root = ET.fromstring(LIVE_STYLE_XML)
        self.assertEqual(resolve_segment_id(root, "‘gm 1’", None), 2)


if __name__ == "__main__":
    unittest.main()