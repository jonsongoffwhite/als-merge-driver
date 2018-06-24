# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
from enum import Enum
from equal import tree_equal
from conflict import Conflict
import os
import webbrowser 
import gzip
import json

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

    def get_return_tracks(self):
        return_tracks = []
        for track in self.tracks:
            if track.type == TrackType.RETURN:
                return_tracks.append(track)
        return return_tracks

    def get_track_with_id(self, id_):
        for track in self.tracks:
            if track.track_id == id_:
                return track

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


        # Get all of the return value mappings for each track in each version
        # Added can be ignored because they won't have any conflicting sends (they are new)
        # As can removed
        # Only care about maintained?
        # We have track.return_map at this point for ours and theirs
        our_same = ours.get_intersection_tracks_compared_to(self)
        their_same = theirs.get_intersection_tracks_compared_to(self)

        
        def get_updated_tracks(branch, branch_same_tracks, base):
            base_tracks = base.tracks
            updated_tracks = []
            for track in branch_same_tracks:
                original_track = [t for t in base_tracks if t.track_id == track.track_id][0]
                # Create mapping of returns
                # See note in equal.py for why this is necessary
                branch_return = branch.get_return_tracks()
                base_return = base.get_return_tracks()
                return_intersection_ids = [t.track_id for t in branch_return if t.track_id in [b.track_id for b in base_return]]
                # Get send ID mapping of these tracks to eachother
                # Their send id is based on their ordering 
                # The key will be the base send ID
                # The value will be that send's ID in the branch track
                send_map = {}
                branch_r_ids = [t.track_id for t in branch_return]
                base_r_ids = [t.track_id for t in base_return]
                for i in return_intersection_ids:
                    br_loc = branch_r_ids.index(i)
                    ba_loc = base_r_ids.index(i)
                    send_map[ba_loc] = br_loc

                if not tree_equal(track.elem, original_track.elem, send_map):
                    updated_tracks.append(track)
                else:
                    pass
            return updated_tracks 


        # Can guarantee only one track in array
        updated_in_ours = get_updated_tracks(ours, our_same, self)
        updated_in_theirs = get_updated_tracks(theirs, their_same, self)

        # Intersection of both of these
        conflicting_track_ids = [t.track_id for t in updated_in_ours if t.track_id in [h.track_id for h in updated_in_theirs]]
        conflicts = [Conflict(*map(lambda x: ET.tostring(x.get_track_with_id(id_).elem).decode() , [self, ours, theirs])) for id_ in conflicting_track_ids] 

        updates = [t for t in updated_in_ours if t.track_id not in conflicting_track_ids]
        updates += [t for t in updated_in_theirs if t.track_id not in conflicting_track_ids]
                    
        for track in updates:
            self.replace_track(track)

        # Can safely add the tracks now
        for track in our_added:
            self.add_track(track)

        for track in their_added:
            self.add_track(track)

        
        ours.reconcile_send_values()
        theirs.reconcile_send_values()
        # Await conflicts here
        # need to make barebones files
        # notify macOS app using webbrowser
        # await file creation of some variety
        # if it's a normal track, get both versions leave returns? which returns?
        # if it's a return track, get a track as well that uses
        # it
        if len(conflicts) > 0:
            conflict_files = []
            for i, conf in enumerate(conflicts):
                # Create a new project from blank.xml to hold the sample project for viewing the conflicts
                sample_root = ET.parse('.merge/blank.xml').getroot()

                # Remove any residual tracks from the blank file's tracks
                sample_tracks = sample_root.find('LiveSet').find('Tracks')
                for c in list(sample_tracks):
                    sample_tracks.remove(c)

                # Add our branch to sample
                sample_ours = ET.fromstring(conf.ours)
                sample_ours.attrib['Id'] = "10"
                sample_ours.find('Name').find('UserName').attrib['Value'] = 'Ours'

                # Add their branch to sample
                sample_theirs = ET.fromstring(conf.theirs)
                sample_theirs.attrib['Id'] = "20"
                sample_theirs.find('Name').find('UserName').attrib['Value'] = 'Theirs'

                # Remove send values
                sample_ours_sends = sample_ours.find('DeviceChain').find('Mixer').find('Sends')
                sample_theirs_sends = sample_theirs.find('DeviceChain').find('Mixer').find('Sends')
                for c in list(sample_ours_sends):
                    sample_ours_sends.remove(c)
                for c in list(sample_theirs_sends):
                    sample_theirs_sends.remove(c)

                # Add our tracks to the sample
                sample_tracks.append(sample_ours)
                sample_tracks.append(sample_theirs)
                sample_tree = ET.ElementTree(sample_root)

                # Create a temporary folder to hold the samples
                temp_folder_name = '.conftemp'
                if not os.path.exists(temp_folder_name):
                    os.makedirs(temp_folder_name)

                # Create the sample file path
                filename = 'conf_' + str(i) + '.xml'
                full_path = temp_folder_name + '/' + filename
                full_als_path = temp_folder_name + '/' + 'conf_' + str(i) + '.als'

                # Write the samples to the folder
                sample_tree.write(full_path, encoding='utf-8', xml_declaration=True)
                with open(full_path, 'rb') as f_in, gzip.open(full_als_path, 'wb') as f_out:
                    f_out.writelines(f_in)

                # Add the file path to the list of sample file paths
                conflict_files.append(full_als_path)

            # Make a call to the url scheme for the jackdaw app
            # appending the paths of the sample files
            url_scheme = 'jackdaw://merge/'
            for cpath in conflict_files:
                url_scheme += cpath + '+'
            url_scheme = url_scheme[:-1]
            webbrowser.open(url_scheme)

            # Wait until the resolution file is present
            # created by the jackdaw app
            import time
            done_file = '.merge/done'
            while not os.path.exists(done_file):
                time.sleep(1)

            resolutions = []

            # Eventually make this so that it reloads from
            # the actual als file so that user edits are saved

            # Open the resolution file
            with open(done_file) as json_data:
                # Load the contents of the file into json
                conf_branch_map = json.load(json_data)
                for conf, branch in conf_branch_map.items():
                    # For each path: true/false ours/theirs
                    # Get the index of the resolution from the original list of files
                    conf_i = conflict_files.index('.conftemp/'+conf)
                    # Get the Conflict object for this version 
                    conflict = conflicts[conf_i]
                    if branch:
                        resolutions.append(ours)
                    else:
                        resolutions.append(theirs)
             

            for i, track_id in enumerate(conflicting_track_ids):
                # Get the chosen version
                chosen_branch = resolutions[i]
                # Get the track from the chosen branch with the selected ID
                to_replace_with = chosen_branch.get_track_with_id(track_id)
                # Replace the track with that ID
                self.replace_track(to_replace_with)
                    

            os.remove('.merge/done')
            import shutil
            shutil.rmtree('.conftemp')

                




        
        self.move_return_tracks_to_end()
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

    # Only use if you can guarantee that there is only one with the id
    # of this track
    def replace_track(self, track):
        remove = []
        for t in self.tracks:
            if t.track_id == track.track_id:
                remove.append(t)
        for t in remove:
            self.tracks.remove(t)
            self.tree.find('LiveSet').find('Tracks').remove(t.elem)
        self.add_track(track)


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
                except KeyError:
                    # create a new entry with default
                    new_mapping[rt.track_id] = 0
            #track.return_map = new_mapping
            track.final_ordered_mapping = [] 
            for rt in return_tracks:
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

    def version_semantically_equal_to(self, other):
        self_track_ids = [t.track_id for t in self.tracks]
        other_track_ids = [t.track_id for t in other.tracks]

        if len(self_track_ids) != len(other_track_ids):
            return False

        if set(self_track_ids) != set(other_track_ids):
            return False

        self_return = self.get_return_tracks()
        other_return = other.get_return_tracks()

        return_intersection_ids = [t.track_id for t in other_return if t.track_id in [b.track_id for b in self_return]]
        # Get send ID mapping of these tracks to eachother
        # Their send id is based on their ordering 
        # The key will be the base send ID
        # The value will be that send's ID in the branch track
        send_map = {}
        other_r_ids = [t.track_id for t in other_return]
        self_r_ids = [t.track_id for t in self_return]
        for i in return_intersection_ids:
            br_loc = other_r_ids.index(i)
            ba_loc = self_r_ids.index(i)
            send_map[ba_loc] = br_loc

        for track in self.tracks:
            other_track = other.get_track_with_id(track.track_id)
            if not tree_equal(track.elem, other_track.elem, send_map):
                return False

        return True
        





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
