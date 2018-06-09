import unittest
import xml.etree.ElementTree as ET
import os, sys
# Add the directory above this file to the path
CODE_DIR = os.path.dirname(__file__)+"/.."
sys.path.append(CODE_DIR)

import equal

class TreeEqualTestCase(unittest.TestCase):

    file_test_equal_1_A = 'test_data/test_equal_1_A.xml'
    file_test_equal_1_B = 'test_data/test_equal_1_B.xml'
    file_test_equal_2_A = 'test_data/test_equal_2_A.xml'

    def load_xml_string_from_file(self, filename):
        with open(filename, 'r') as f:
            file_string = f.read()
            return file_string

    def test_same_xml_equal(self):
        str_a = self.load_xml_string_from_file(self.file_test_equal_1_A)
        root_a = ET.fromstring(str_a)
        root_b = ET.fromstring(str_a)
        self.assertNotEqual(root_a, root_b)
        self.assertTrue(equal.tree_equal(root_a, root_b, []))

    def test_semantically_different_xml_not_equal(self):
        str_a = self.load_xml_string_from_file(self.file_test_equal_2_A)
        str_b = self.load_xml_string_from_file(self.file_test_equal_1_A)
        root_a = ET.fromstring(str_a)
        root_b = ET.fromstring(str_b)
        self.assertNotEqual(root_a, root_b)
        self.assertFalse(equal.tree_equal(root_a, root_b, []))
    
    def test_semantically_equal_xml_equal(self):
        str_a = self.load_xml_string_from_file(self.file_test_equal_1_A)
        str_b = self.load_xml_string_from_file(self.file_test_equal_1_B)
        root_a = ET.fromstring(str_a)
        root_b = ET.fromstring(str_b)
        self.assertNotEqual(root_a, root_b)
        self.assertTrue(equal.tree_equal(root_a, root_b, []))
    
    def test_empty_trees_equal(self):
        empty_a = ET.ElementTree().getroot()
        empty_b = ET.ElementTree().getroot()
        self.assertTrue(equal.tree_equal(empty_a, empty_b, []))



if __name__ == '__main__':
    unittest.main()