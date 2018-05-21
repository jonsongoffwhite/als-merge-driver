'''

    Notable .als xml constituents

    Ableton
        LiveSet
            Tracks
                MidiTrack {id}
                AudioTrack {id}
                ReturnTrack {id}
    
    Within Device Chain:
        LastPresetRef name (could be used for ID if instrument has changed)


    Ignorable (choose 1) .als xml constituents

        NextPointeeId
        ScrollerTimePreserver
        AutomationTarget


    Notes:

        Adding tracks will assign them a new ID which is obvious during merge
        however, if an existing track is edited (e.g. change instrument) then it is less
        obvious - need a certain way to detect (instrument id somewhere? name?)


    Cases to consider:
        Basic:
            Adding new track




    Calculate new and removed tracks for both of the branches
    Any collisions can be rectified, if there are collisions
    Even when brand new tracks are added, they seem to end up with same id,
    therefore always collide, even if created independently of eachother.
    Log all track IDs, in base, branch_a and branch_b and ensure no collisions


    Issues come across:
        - Return tracks out of order
        - Return track values on tracks merged in where the return track did not exist?



    IDs that must be unique within a 'Track' all seem to be:
        AutomationTarget
        ModulationTarget
        VolumeModulationTarget
        TranspositionModulationTarget
        GrainSizeModulationTarget
        FluxModulationTarget
        SampleOffsetModulationTarget




'''

import sys
import xml.etree.ElementTree as ET

COLLIDABLE_TAG = [
        "AutomationTarget",
        "ModulationTarget",
        "VolumeModulationTarget",
        "TranspositionModulationTarget",
        "GrainSizeModulationTarget",
        "FluxModulationTarget",
        "SampleOffsetModulationTarget"
]

print(sys.argv)

# Get the tracks element from Ableton Live XML (ALX)
def get_tracks_element(root):
    return root.find('LiveSet').find('Tracks')

# Get the track elements from ALX
def get_tracks(root):
    return list(get_tracks_element(root))

# Get the track ids for all tracks in ALX
def get_track_ids(root):
    return [id_ for id_ in [track.attrib['Id'] for track in list(get_tracks_element(root))]]

# Get ids of changed tracks in branch compared to base
# 'added' tracks appear in branch and not in base
# 'removed' tracks appear in base and not in branch
def get_track_changes_ids(base, branch):

    base_track_ids = get_track_ids(base)
    branch_track_ids = get_track_ids(branch) 

    added = []
    removed = []

    for id_ in base_track_ids:
        if id_ not in branch_track_ids:
            removed.append(id_)

    for id_ in branch_track_ids:
        if id_ not in base_track_ids:
            added.append(id_)

    return (added, removed)

# Gets track node of tracks that are in branch
# that are not in base
def get_added_tracks(base, branch):
    base_tracks = get_tracks(base)
    branch_tracks = get_tracks(branch)

    base_track_ids = get_track_ids(base)

    added = []
    for node in branch_tracks:
        if node.attrib['Id'] not in base_track_ids:
            added.append(node)
    return added


# Gets track node of tracks that are in base
# that are not in branch
def get_removed_tracks(base, branch):
    return get_added_tracks(branch, base)


# Reassigns IDs to sensitive nodes if they share their ID with another node
def amend_ids(root):
    # Get all nodes with Id values that should not collide
    nodes = get_nodes_with_collidable_ids(root, [])

    # Find duplicate entries and assigned them next available id
    taken_ids = []
    duplicate_nodes = []
    for node in nodes:
        if node.attrib['Id'] not in taken_ids:
            taken_ids.append(node.attrib['Id'])
        else:
            duplicate_nodes.append(node)
            print(node.tag + " " + node.attrib['Id'] + "\n")
    #print(duplicate_nodes)
    
    # Reassigned those with duplicates
    id_ = max(list(map(lambda x: int(x), taken_ids))) + 1

    for node in duplicate_nodes:
        node.attrib['Id'] = str(id_)
        id_ += 1

# Get list of nodes that are sensitive to collision
def get_nodes_with_collidable_ids(node, nodes):
    children = list(node)
    if node.tag in COLLIDABLE_TAG:
        nodes.append(node)
    for child in children:
        get_nodes_with_collidable_ids(child, nodes)
    return nodes

def get_sends(track):
    return track.find('DeviceChain').find('Mixer').find('Sends')

def run(argv=None):
    if not argv:
        # Ignore program name
        argv = sys.argv[1:]

    if len(argv) < 4:
        sys.stderr.write("Please input three files and specify an output location")
        exit(-1)

    output_filename = argv[3]

    base_filename = argv[0]
    ours_filename = argv[1]
    theirs_filename = argv[2] 

    tree_base = ET.parse(argv[0])
    tree_out = ET.parse(argv[0])
    tree_ours = ET.parse(argv[1])
    tree_theirs = ET.parse(argv[2])
    
    root_base = tree_base.getroot()
    root_out = tree_out.getroot()
    root_ours = tree_ours.getroot()
    root_theirs = tree_theirs.getroot()

    # Get Tracks
    base_tracks = get_tracks(root_base)
    our_added_tracks = get_added_tracks(root_base, root_ours)
    our_removed_tracks = get_removed_tracks(root_base, root_ours)
    their_added_tracks = get_added_tracks(root_base, root_theirs)
    their_removed_tracks = get_removed_tracks(root_base, root_theirs)

    # Get Return tracks
    def get_return_tracks(tracks):
        return [track for track in tracks if track.tag == 'ReturnTrack']

    base_return_tracks = get_return_tracks(base_tracks)
    our_added_return_tracks = get_return_tracks(our_added_tracks)
    our_removed_return_tracks = get_return_tracks(our_removed_tracks)
    their_added_return_tracks = get_return_tracks(their_added_tracks)
    their_remove_return_tracks = get_return_tracks(their_removed_tracks)

    # Get original send value on each track for each of the return tracks
    # First from the base set of tracks
    # Then ours, then theirs (choose?)

    base_return_values = {}
    base_track_id_to_return_values = {}
    for track in base_tracks:
        sends = get_sends(track)
        send_holders = sends.findAll('TrackSendHolder')
        # Sort based on Id which is the order that the return tracks appear
        ordered_send_holders = sorted(send_holders, key=lambda x: int(x.attrib['Id']))

        # Assumes ordering
        send_values = [s.find('Send').find('Manual').attrib['Value'] for s in list(sends)]


    # Get IDs
    base_track_ids = get_track_ids(root_base)
    our_new_track_ids, our_removed_track_ids = get_track_changes_ids(root_base, root_ours)
    their_new_track_ids, their_removed_track_ids = get_track_changes_ids(root_base, root_theirs)

    # Calculate collisions
    # ids that are in both ours and theirs but not in base are problematic
    # there is no way that these could be intended to be the same track
    collisions = list(set(our_new_track_ids) & set(their_new_track_ids))
    
    # Assign new ids to colliding 'their' tracks then add them into copy of base
    taken_ids = list(set(base_track_ids) | set(our_new_track_ids) | set([id_ for id_ in their_new_track_ids if id_ not in collisions]))

    # Id change to apply to theirs 
    mapping = {}

    for id_ in collisions:
        # Start at 10 as worried about special ids below this
        new_id = 10
        while new_id in taken_ids:
            new_id += 1

        mapping[id_] = new_id
        taken_ids.append(new_id)


    # Apply changes to base copy
    # Need to decide how to choose whether to remove or keep tracks from branches
    # Keep all for now - don't remove any unless removed in both ours and theirs
    tracks = get_tracks_element(root_out)

    to_remove = list(set(our_removed_track_ids) & set(their_removed_track_ids))

    for track in list(tracks):
        if track.attrib['Id'] in to_remove:
            tracks.remove(track)

    # Add new ones from ours
    our_track_elems = get_tracks_element(root_ours) 

    for track in list(our_track_elems):
        if track.attrib['Id'] in our_new_track_ids:
            tracks.append(track)

    # Add new ones from theirs without collisions, and ones without collision
    their_track_elems = get_tracks_element(root_theirs)
    for track in list(their_track_elems):
        id_ = track.attrib['Id']
        if id_ in their_new_track_ids:
            if id_ in mapping:
                track.attrib['Id'] = str(mapping[id_])
            tracks.append(track)
        
    print(list(tracks))
    for i in tracks:
        print(i.attrib['Id'])

    # Put return tracks last (this is bad)
    return_tracks = []
    for track in list(tracks):
        if track.tag == 'ReturnTrack':
            return_tracks.append(track)
            print(track)
            tracks.remove(track)
        else:
            print('not return: ' + track.tag)

    for track in return_tracks:
        tracks.append(track)

    print('tracks')
    print(list(tracks))




    root = tree_out.getroot()
    amend_ids(root)


    tree_out.write(output_filename, encoding='utf-8', xml_declaration=True)


if __name__ == '__main__':
    run()
