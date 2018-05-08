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


'''




import sys
import xml.etree.ElementTree as ET

print(sys.argv)

def get_tracks_element(root):
    return root.find('LiveSet').find('Tracks')

def get_track_ids(root):
    return [id_ for id_ in [track.attrib['Id'] for track in list(get_tracks_element(root))]]


def get_track_changes(base, branch):

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


    base_tracks = get_track_ids(root_base)
    our_new_tracks, our_removed_tracks = get_track_changes(root_base, root_ours)
    their_new_tracks, their_removed_tracks = get_track_changes(root_base, root_theirs)

    # Calculate collisions
    # ids that are in both ours and theirs but not in base are problematic
    # there is no way that these could be intended to be the same track
    collisions = list(set(our_new_tracks) & set(their_new_tracks))
    
    # Assign new ids to colliding 'their' tracks then add them into copy of base
    taken_ids = list(set(base_tracks) | set(our_new_tracks) | set([id_ for id_ in their_new_tracks if id_ not in collisions]))

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

    to_remove = list(set(our_removed_tracks) & set(their_removed_tracks))

    for track in list(tracks):
        if track.attrib['Id'] in to_remove:
            tracks.remove(track)

    # Add new ones from ours
    our_track_elems = get_tracks_element(root_ours) 

    for track in list(our_track_elems):
        if track.attrib['Id'] in our_new_tracks:
            tracks.append(track)

    # Add new ones from theirs without collisions, and ones without collision
    their_track_elems = get_tracks_element(root_theirs)
    for track in list(their_track_elems):
        id_ = track.attrib['Id']
        if id_ in their_new_tracks:
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

    tree_out.write(output_filename, encoding='utf-8', xml_declaration=True)




if __name__ == '__main__':
    run()
