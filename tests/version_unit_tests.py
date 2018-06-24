import unittest
import xml.etree.ElementTree as ET
import os, sys
# Add the directory above this file to the path
CODE_DIR = os.path.dirname(__file__)+"/.."
sys.path.append(CODE_DIR)

from version import Version, Track, TrackType

class VersionUnitTestCase(unittest.TestCase):

    file_test_version_1_A = "test_data/test_version_1_A.xml"
    file_test_version_2_A = "test_data/test_version_2_A.xml"

    def setUp(self):
        version_1_string = self.load_xml_string_from_file(self.file_test_version_1_A)
        self.version_1 = Version(ET.fromstring(version_1_string))
        version_2_string = self.load_xml_string_from_file(self.file_test_version_2_A)
        self.version_2 = Version(ET.fromstring(version_2_string))

    def load_xml_string_from_file(self, filename):
        with open(filename, 'r') as f:
            file_string = f.read()
            return file_string
    
    def test_add_track(self):
        track_list = self.version_1.tracks
        tracks_et = self.version_1.tree.find('LiveSet').find('Tracks')
        new_track = self.version_2.tracks[0]
        self.assertTrue(len(track_list) == 9)
        self.assertTrue(len(list(tracks_et)) == 9)
        self.version_1.add_track(new_track)
        self.assertTrue(len(track_list) == 10)
        self.assertTrue(len(list(tracks_et)) == 10)

    def test_reconcile_send_values(self):
        """
        Test that final mapping of return to send values is
        successfully transformed into ordered mapping
        according to resulting return track order
        """
        return_tracks = self.version_1.get_return_tracks()
        final_return_track = return_tracks[-1]
        for t in self.version_1.tracks:
            for r in return_tracks[:-1]:
                t.return_map[r.track_id] = 0.5
            del t.return_map[final_return_track.track_id]
        self.version_1.reconcile_send_values()
        for t in self.version_1.tracks:
            self.assertTrue(t.final_ordered_mapping != None)
            self.assertTrue(t.final_ordered_mapping == [0.5, 0.5, 0])

    def test_move_return_tracks_to_end(self):
        """
        Test that return tracks are moved to the end of the
        list of tracks
        """
        from random import shuffle
        while(self.version_1.tracks[-1].type == TrackType.RETURN):
            shuffle(self.version_1.tracks)
        self.version_1.move_return_tracks_to_end()
        self.assertTrue(self.version_1.tracks[-1].type == TrackType.RETURN)
        self.assertTrue(self.version_1.tracks[-2].type == TrackType.RETURN)
        self.assertTrue(self.version_1.tracks[-3].type == TrackType.RETURN)
        

    def test_amend_sends_pre(self):
        """
        Test that the sends pre element is updated to account
        for the new number of return tracks
        """
        self.version_1.move_return_tracks_to_end()
        self.assertTrue(len(list(self.version_1.tree.find('LiveSet').find('SendsPre'))) == 3)
        self.version_1.add_track(self.version_2.get_return_tracks()[0])
        self.version_1.amend_sends_pre()
        self.assertTrue(len(list(self.version_1.tree.find('LiveSet').find('SendsPre'))) == 4)

    def test_amend_global_id_collisions(self):
        """
        Test that all colliding global ids within the ET
        are made unique by generating a new value for
        each of the collisions
        """


    def amend_track_collisions(self):
        """
        Test that any tracks that share an ID
        are made to have new unique ids
        """
        self.version_1.tracks[0].track_id = 555
        self.version_1.tracks[0].elem.attrib['Id'] = str(555)
        self.version_1.tracks[1].track_id = 555
        self.version_1.tracks[1].elem.attrib['Id'] = str(555)

        self.version_1.amend_track_collisions()
        changed = self.version_1.tracks[0].track_id != self.version_1.tracks[1].track_id
        elem_changed = self.version_1.tracks[0].elem.attrib['Id'] != self.version_1.tracks[1].elem.attrib['Id']
        self.assertTrue(changed and elem_changed)

    def test_generate_sends(self):
        """
        Test that the sends in final_ordered_mapping for each
        track are translated correctly into the ET
        """
        for t in self.version_1.tracks:
            sends = t.elem.find('DeviceChain').find('Mixer').find('Sends')
            for s in list(sends):
                sends.remove(s)
        self.version_1.reconcile_send_values()
        self.version_1.generate_sends()
        for t in self.version_1.tracks:
            sends = t.elem.find('DeviceChain').find('Mixer').find('Sends')
            self.assertTrue(len(list(sends)) == 3)

if __name__ == '__main__':
    unittest.main()