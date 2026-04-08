import unittest
import xml.etree.ElementTree as ET

from wkanno.labels import resolve_segment_id


PV_STYLE_XML = """
<things>
  <parameters>
    <userBoundingBox id="14" name="WM 1" topLeftX="0" topLeftY="1639" topLeftZ="1443" width="120" height="250" depth="250" />
    <userBoundingBox id="15" name="WM 2" topLeftX="5" topLeftY="2301" topLeftZ="1503" width="120" height="250" depth="250" />
  </parameters>
  <volume>
    <segments>
      <segment id="16" name="Annotations WM 1" anchorPositionX="105" anchorPositionY="1819" anchorPositionZ="1651" />
      <segment id="17" name="Annotations WM 2" anchorPositionX="35" anchorPositionY="2500" anchorPositionZ="1629" />
    </segments>
  </volume>
</things>
"""


class ResolveSegmentIdTests(unittest.TestCase):
    def test_falls_back_to_anchor_inside_box(self) -> None:
        root = ET.fromstring(PV_STYLE_XML)
        self.assertEqual(resolve_segment_id(root, "WM 1", None), 16)
        self.assertEqual(resolve_segment_id(root, "WM 2", None), 17)


if __name__ == "__main__":
    unittest.main()