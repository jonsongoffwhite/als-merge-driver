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

#TRACK_SEND_HOLDER = """<TrackSendHolder Id="0"><Send><LomId Value="0" /><Manual Value="0.0003162277571" /><MidiControllerRange><Min Value="0.0003162277571" /><Max Value="1" /></MidiControllerRange><AutomationTarget Id="8631"><LockEnvelope Value="0" /></AutomationTarget><ModulationTarget Id="8632"><LockEnvelope Value="0" /></ModulationTarget></Send><Active Value="true" /></TrackSendHolder>"""

COLLIDABLE_TAG = [
        "AutomationTarget",
        "ModulationTarget",
        "VolumeModulationTarget",
        "TranspositionModulationTarget",
        "GrainSizeModulationTarget",
        "FluxModulationTarget",
        "SampleOffsetModulationTarget"
]

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
        for track in self.tracks:
            mapping = {}
            for index in track.preliminary_return_map:
                value = track.preliminary_return_map[index]
                mapping[ordered_return_tracks[index].track_id] = value    
            track.set_return_map(mapping)

    def merge_with(self, ours, theirs):

        our_added = ours.get_added_tracks_compared_to(self)
        their_added = theirs.get_added_tracks_compared_to(self)

        our_removed = ours.get_removed_tracks_compared_to(self)
        their_removed = theirs.get_removed_tracks_compared_to(self)

       
        # Any removed from both
        our_removed_ids = [t.track_id for t in our_removed]
        their_removed_ids = [t.track_id for t in their_removed]
        both_removed_ids = [t for t in our_removed_ids if t in their_removed_ids]
        
        # Remove the tracks from self
        both_removed = [t for t in self.tracks if t.track_id in both_removed_ids]
        self.tracks = [t for t in self.tracks if t.track_id not in both_removed_ids]   
         
        for t in both_removed:
            # NOTE: This might not work if merging multiple times as the elements
            # will have changed after reconcilliation
            self.tree.find('LiveSet').find('Tracks').remove(t.elem)


        for track in our_added:
            self.add_track(track)

        for track in their_added:
            self.add_track(track)

        self.move_return_tracks_to_end()
        self.reconcile_send_values()

        # Get all of the return value mappings for each track in each version
        # Added can be ignored because they won't have any conflicting sends (they are new)
        # As can removed
        # Only care about maintained?
        # We have track.return_map at this point for ours and theirs
        our_same = ours.get_intersection_tracks_compared_to(self)
        their_same = theirs.get_intersection_tracks_compared_to(self)

        # Need to establish whether to favour ours or theirs, or base?
        # Offer a choice?
        for track in our_same:
            # Get corresponding base track that is same
            # We can guarantee that the array below will be 1 long 
            base_track = [t for t in self.tracks if t.track_id == track.track_id][0]
            # What to do about new entries?
            # What if a return track that we are about to query by its ID has been deleted?
            our_mapping = track.return_map
            base_mapping = base_track.return_map
            for key in base_mapping:
                if key in our_mapping:
                    our_value = our_mapping[key]
                    current_value = base_mapping[key]
                    if current_value != our_value:
                        # Just overwrite it for now
                        print("overwriting value")
                        print("was: " + str(current_value))
                        print("now: " + str(our_value))
                        base_mapping[key] = our_value
        
 
        


        # reconcile again to account for changed values
        self.reconcile_send_values()

        self.amend_track_collisions()
        self.generate_sends()
        self.amend_global_id_collisions()
        self.amend_sends_pre()



    # Returns a list of tracks included in this version that are not included
    # the version passed to the method 
    # Checks by the ID of the tracks
    def get_added_tracks_compared_to(self, version):
        their_tracks = version.tracks
        their_track_ids = [t.track_id for t in their_tracks]
        return [t for t in self.tracks if t.track_id not in their_track_ids]

    # Inversion of added tracks - added tracks relative to provided version
    def get_removed_tracks_compared_to(self, version):
        return version.get_added_tracks_compared_to(self)

    def get_intersection_tracks_compared_to(self, version):
        their_tracks = version.tracks
        their_track_ids = [t.track_id for t in their_tracks]
        return [t for t in self.tracks if t.track_id in their_track_ids]

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
    #
    # Does not mutate ETree
    # 
    # Doesn't work properly
    def reconcile_send_values(self):
        # Get all return tracks
        return_tracks = [r for r in self.tracks if r.type == TrackType.RETURN]

        # Put correct sends for each return track,
        # adding them if they do not exist
        # in track.final_ordered_mapping
        for track in self.tracks:
            new_mapping = {}
            for rt in return_tracks:
                try:
                    value = track.return_map[rt.track_id]
                    new_mapping[rt.track_id] = value
                    print('found existing send')
                    print(value)
                except KeyError:
                    # create a new entry with default
                    new_mapping[rt.track_id] = 0
                    print('create zero send')
            #track.return_map = new_mapping
            track.final_ordered_mapping = [] 
            for rt in return_tracks:
                print(new_mapping)
                track.final_ordered_mapping.append(new_mapping[rt.track_id])


    def move_return_tracks_to_end(self):
        tracks_copy = []
        return_tracks = []
        for track in self.tracks:
            if track.type == TrackType.RETURN:
                return_tracks.append(track)
            else:
                tracks_copy.append(track)
        self.tracks = tracks_copy + return_tracks

            
        for track in return_tracks:
            self.tree.find('LiveSet').find('Tracks').remove(track.elem)
            self.tree.find('LiveSet').find('Tracks').append(track.elem)



    # Check and amend collisions in IDs before writing
    # Make sure return tracks all at end?
    def write(self, filename):
        tree = ET.ElementTree(self.tree)
        tree.write(filename, encoding='utf-8', xml_declaration=True)

    def _dump(self, filename):
        tree = ET.ElementTree(self.tree)
        tree.write(filename, encoding='utf-8', xml_declaration=True)

    def amend_sends_pre(self):
        return_tracks = [t for t in self.tracks if t.type == TrackType.RETURN]
        return_tracks_count = len(return_tracks)
        sp_str = """<SendPreBool Id="3" Value="false" />"""
        sp = self.tree.find('LiveSet').find('SendsPre')
        curr_count = len(list(sp))
        for i in range(curr_count, return_tracks_count):
            elem = ET.fromstring(sp_str)
            elem.attrib['Id'] = str(i)
            sp.append(elem)


    # Visit every node in the tree and document its ID
    # If a duplicate ID is present, reassigned new ids
    def amend_global_id_collisions(self):
        # COLLIDABLE_TAG
        used_ids = []
        duplicate_nodes = []
        
        def check_ids(node):
            if node.tag in COLLIDABLE_TAG:
                id_ = int(node.attrib['Id'])
                if id_ in used_ids:
                    duplicate_nodes.append(node)
                else:
                    used_ids.append(id_)
            for c in list(node):
                check_ids(c)

        check_ids(self.tree)
        print(len(duplicate_nodes))

        new_id = max(used_ids)
        for node in duplicate_nodes:
            new_id += 1
            node.attrib['Id'] = str(new_id)


    def amend_track_collisions(self):
        track_ids = [t.track_id for t in self.tracks]
        if len(set(track_ids)) == len(track_ids):
            # No collisions
            return
        
        # Gather the tracks that need their IDs changed
        used_ids = []
        collided_tracks = [] 
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

    def generate_sends(self):
        tracks = self.tracks
        returns = [t for t in tracks if t.type == TrackType.RETURN]
        
        # Remove current sends
        for track in tracks:
            print(track.final_ordered_mapping)
            track_sends = track.elem.find('DeviceChain').find('Mixer').find('Sends')
            old_sends = [sh for sh in track_sends]
            for sh in old_sends:
                track_sends.remove(sh)

        # Add new sends
        for track in tracks:
            track_sends = track.elem.find('DeviceChain').find('Mixer').find('Sends')
            for i, rt in enumerate(returns):
                sh_elem = ET.fromstring(TRACK_SEND_HOLDER.strip())
                sh_elem.attrib['Id'] = str(i)
                # de activate sends if track is a return track
                # if track.type == TrackType.RETURN:
                #    print("deactivating send for return track")
                #    sh_elem.find('Active').attrib['Value'] = "false"
                sh_elem.find('Send').find('Manual').attrib['Value'] = str(track.final_ordered_mapping[i])
                track_sends.append(sh_elem)
                

    def return_track_count(self):
        return len([r for r in self.tracks if r.type == TrackType.RETURN])




class Track():

    def __init__(self, elem):
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
        print(self.preliminary_return_map)
        self.return_map = None

        # The type of track
        if self.elem.tag == 'MidiTrack':
            self.type = TrackType.MIDI
        elif self.elem.tag == 'AudioTrack':
            self.type = TrackType.AUDIO
        else:
            self.type = TrackType.RETURN

    # Issues with references?
    def set_track_id(self, new_id):
        self.track_id = new_id
        self.elem.attrib['Id'] = str(new_id)

    # mapping of return track objects to values
    def set_return_map(self, mapping):
        self.return_map = mapping


class TrackType(Enum):
    MIDI = 0
    AUDIO = 1
    RETURN = 2
