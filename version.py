import xml.etree.ElementTree as ET
from enum import Enum

class Version():
    
    def __init__(tree):

        # The ElementTree for the whole version
        self.tree = tree

        # All tracks in this version
        self.tracks = [Track(elem) for elem in list(tree.find('LiveSet').find('Tracks'))]

    def get_added_tracks_compared_to(version):
        pass

    def get_removed_tracks_compared_to(version):
        pass

class Track():

    def __init__(elem):
        # The ElementTree track node
        self.elem = elem

        # The id of the track
        self.track_id = int(self.elem.attrib['Id'])

        # The values attached to each return track, ordered
        # Should be substituted for mapping of return track
        # to value later
        sends = list(self.elem.find('DeviceChain').find('Mixer').find('Sends'))
        self.preliminary_return_map = {
            int(send.attrib['Id']): float(send.find('Send').find('Manual').attrib['Value'])
                for send in sends
        }

        # The type of track
        if self.elem.tag == 'MidiTrack':
            self.type = TrackType.MIDI
        elif self.elem.tag == 'AudioTrack':
            self.type = TrackType.AUDIO
        else:
            self.type = TrackType.RETURN


class TrackType(Enum):
    MIDI = 0
    AUDIO = 1
    RETURN = 2
