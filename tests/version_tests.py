import unittest
import xml.etree.ElementTree as ET
import os, sys
# Add the directory above this file to the path
CODE_DIR = os.path.dirname(__file__)+"/.."
sys.path.append(CODE_DIR)

from version import Version

class VersionMethodTestCase(unittest.TestCase):

    file_test_version_1_A = "test_data/test_version_1_A.xml"
    file_test_version_2_A = "test_data/test_version_2_A.xml"
    file_test_version_2_B = "test_data/test_version_2_B.xml"

    def load_xml_string_from_file(self, filename):
        with open(filename, 'r') as f:
            file_string = f.read()
            return file_string

    def setUp(self):
        version_1_string = self.load_xml_string_from_file(self.file_test_version_1_A)
        self.version_1 = Version(ET.fromstring(version_1_string))

    def test_init_initalises_tracks_property(self):
        expected_track_ids = [
            12, 13, 17, 18, 8, 14, 2, 16, 3,
        ]
        version_track_ids = [t.track_id for t in self.version_1.tracks]
        self.assertEqual(set(expected_track_ids), set(version_track_ids))
        self.assertEqual(len(expected_track_ids), len(version_track_ids))

    def test_get_return_tracks(self):
        expected_return_track_ids = [2, 16, 3]
        version_return_track_ids = [t.track_id for t in self.version_1.get_return_tracks()]
        self.assertEqual(set(expected_return_track_ids), set(version_return_track_ids))
        self.assertEqual(len(expected_return_track_ids), len(version_return_track_ids))

    def test_merge_with_self_and_self_produces_self(self):
        version_1_copy_string_1 = self.load_xml_string_from_file(self.file_test_version_1_A)
        version_1_copy_1 = Version(ET.fromstring(version_1_copy_string_1))
        version_1_copy_string_2 = self.load_xml_string_from_file(self.file_test_version_1_A)
        version_1_copy_2 = Version(ET.fromstring(version_1_copy_string_2))

        version_1_copy_1.merge_with(version_1_copy_1, version_1_copy_2)
        self.assertTrue(self.version_1.version_semantically_equal_to(version_1_copy_1))

        
    def test_merge_with_self_and_branch_produces_branch(self):
        version_1_copy_string = self.load_xml_string_from_file(self.file_test_version_1_A)
        version_1_copy = Version(ET.fromstring(version_1_copy_string))
        version_2_copy_string = self.load_xml_string_from_file(self.file_test_version_2_A)
        version_2_copy = Version(ET.fromstring(version_2_copy_string))

        version_1_copy.merge_with(version_1_copy, version_2_copy)
        self.assertFalse(self.version_1.version_semantically_equal_to(version_2_copy))
        self.assertTrue(version_1_copy.version_semantically_equal_to(version_2_copy))

    
    def test_merge_with_a_and_b_with_no_conflicts_produces_correct_combination(self):
        # Can check for presence of correct tracks, return tracks and sends here
        version_1_string = self.load_xml_string_from_file(self.file_test_version_1_A)
        version_2_A_string = self.load_xml_string_from_file(self.file_test_version_2_A)
        version_2_B_string = self.load_xml_string_from_file(self.file_test_version_2_B)

        version_1 = Version(ET.fromstring(version_1_string))
        version_2_A = Version(ET.fromstring(version_2_A_string))
        version_2_B = Version(ET.fromstring(version_2_B_string))

        version_1.merge_with(version_2_A, version_2_B)
        version_1.write('asdf.xml')
        self.assertFalse(self.version_1.version_semantically_equal_to(version_1))
        self.assertFalse(version_1.version_semantically_equal_to(version_2_A))
        self.assertFalse(version_1.version_semantically_equal_to(version_2_B))
        

        # Check tracks from both
        # Check one effective name contains: Campfire, Bright Marimba
        campfire = False
        bright_marimba = False
        for track in version_1.tracks:
            if "Campfire" in track.elem.find('Name').find('EffectiveName').attrib['Value']:
                campfire = True
            
            if "Bright Marimba" in track.elem.find('Name').find('EffectiveName').attrib['Value']:
                bright_marimba = True
        
        self.assertTrue(campfire)
        self.assertTrue(bright_marimba)
        

if __name__ == '__main__':
    unittest.main()