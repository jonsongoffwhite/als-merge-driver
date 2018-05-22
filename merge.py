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
from version import Version, Track

COLLIDABLE_TAG = [
        "AutomationTarget",
        "ModulationTarget",
        "VolumeModulationTarget",
        "TranspositionModulationTarget",
        "GrainSizeModulationTarget",
        "FluxModulationTarget",
        "SampleOffsetModulationTarget"
]

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

    base_version = Version(root_base)
    our_version = Version(root_ours)
    their_version = Version(root_theirs)

    base_version.merge_with(our_version, their_version)

    # This is all done within write but doing separately for debugging
    #base_version.move_return_tracks_to_end()
    #base_version.reconcile_send_values()
    #base_version.amend_track_collisions()
    #base_version.generate_sends()
    #base_version.amend_global_id_collisions()

    base_version.write(output_filename)


if __name__ == '__main__':
    run()
