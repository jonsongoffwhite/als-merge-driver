import xml.etree.ElementTree as ET
from enum import Enum

TRACK_SEND_HOLDER = """

        <TrackSendHolder Id="0">
                <Send>
                        <LomId Value="0" />
                        <Manual Value="0.0003162277571" />
                        <MidiControllerRange>
                                <Min Value="0.0003162277571" />
                                <Max Value="1" />
                        </MidiControllerRange>
                        <AutomationTarget Id="8631">
                                <LockEnvelope Value="0" />
                        </AutomationTarget>
                        <ModulationTarget Id="8632">
                                <LockEnvelope Value="0" />
                        </ModulationTarget>
                </Send>
                <Active Value="true" />
        </TrackSendHolder>
                    """

class Version():
    
    def __init__(self, tree):

        # The ElementTree for the whole version
        self.tree = tree

        # All tracks in this version
        self.tracks = [Track(elem) for elem in list(tree.find('LiveSet').find('Tracks'))]

        ordered_return_tracks = [t for t in self.tracks if t.type == TrackType.RETURN]
        # Set a mapping from track object to value in each track,
        # rather than the return track index
        num_tracks = len(ordered_return_tracks)
        for track in tracks:
            mapping = {}
            for index, value in track.preliminary_return_map:
                mapping[ordered_return_tracks[index]] = value    
            track.set_return_map(mapping)


    # Returns a list of tracks included in this version that are not included
    # the version passed to the method 
    # Checks by the ID of the tracks
    def get_added_tracks_compared_to(self, version):
        their_tracks = version.tracks
        their_track_ids = [t.track_id for t in their_tracks]
        return [t for t in self.tracks if track.track_id not in their_track_ids]

    # Inversion of added tracks - added tracks relative to provided version
    def get_removed_tracks_compared_to(self, version):
        return version.get_added_tracks_compared_to(self)

    def add_track(self, track):
        if track.type == TrackType.RETURN:
            # where in the order was it added?
            # update values accordingly
            # currently just add it last?
            #new_send = ET.fromstring(TRACK_SEND_HOLDER)
            #new_send.attrib['Id'] = str(len(self.return_track_count()))
            #for track in self.tracks:
            #    track.elem.find('DeviceChain').find('Mixer').find('Sends').append(new_send)
            pass

        self.tracks.append(track)
        self.tree.find('LiveSet').find('Tracks').append(track.elem)

    # take return values from the stored dictionary in each track and
    # make sure they are reflected in the xml
    #
    # decide on an ordering of return tracks
    # fill in the send values according to that ordering
    # using the mappings in each of the tracks
    #
    # All tracks must be added before calling
    def reconcile_send_values(self):
        # Get all return tracks
        return_tracks = [r for r in self.tracks if r.type == TrackType.RETURN]

        # Make sure they are all at the end?

        # Put correct sends for each return track,
        # adding them if they do not exist
        for track in self.tracks:
            new_mapping = {}
            for rt in return_tracks:
                try:
                    value = track.return_map[rt]
                    new_mapping[rt] = value
                except KeyError:
                    # create a new entry with default
                    new_mapping[rt] = 0
            #track.return_map = new_mapping
            track.final_ordered_mapping = [] 
            for rt in return_tracks:
                track.final_ordered_mapping.append(new_mapping[rt])


    # Check and amend collisions in IDs before writing
    # Make sure return tracks all at end?
    def write(self, filename):
        self.reconcile_send_values()
        self.amend_track_collisions()
        self.generate_sends()
        self.amend_global_id_collisions()
        self.tree.write(filename)
        pass

    def amend_global_id_collisions():
        pass

    def amend_track_collisions(self):
        track_ids = [t.track_id for t in self.tracks]
        if len(set(track_ids)) == len(track_ids):
            # No collisions
            return
        
        # Gather the tracks that need their IDs changed
        used_ids = []
        collided_tracks
        for track in self.tracks:
            if track.track_id not in used_ids:
                used_ids.append(track.track_id)
            else:
                collided_tracks.append(track)

        # Get the max current track id and add one for first available
        next_id = max(used_ids) + 1
        for t in collided_tracks:
            t.set_track_id(next_id)
            next_id += 1

    def generate_sends():
        pass

    def return_track_count(self):
        return len([r for r in self.tracks if r.type == TrackType.RETURN])




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
        self.return_map = None

        # The type of track
        if self.elem.tag == 'MidiTrack':
            self.type = TrackType.MIDI
        elif self.elem.tag == 'AudioTrack':
            self.type = TrackType.AUDIO
        else:
            self.type = TrackType.RETURN

    # Issues with references?
    def set_track_id(new_id):
        self.track_id = new_id
        self.elem.attrib['Id'] = str(new_id)

    # mapping of return track objects to values
    def set_return_map(mapping):
        self.return_map = mapping


class TrackType(Enum):
    MIDI = 0
    AUDIO = 1
    RETURN = 2
