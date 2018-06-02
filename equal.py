# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET


IGNORE_ATTRIB_FOR = {
    'IsContentSelected': ['Value'],
    'IsArmed': ['Value'],
    'RelativePathElement': ['Id'],
    'FileRef': ['Id'],
    'SelectedDevice': ['Value'],
    'SelectedEnvelope': ['Value'],
    'LastSelectedTimeableIndex': ['Value'],
    'LastSelectedClipEnvelopeIndex': ['Value'],
    'VstPreset': ['Id'],
    'TrackSendHolder': ['Id'],
    'AutomationTarget': ['Id'],
}

IGNORE_ALWAYS = {
}

def tree_equal(e1, e2, send_map):
    """
    Calculates deep equality of two ElementTree Elements,
    leaving out unimportant circumstantial values such as
    unique IDs 

    Ignore:
        IsContentSelected attrib: Value
        IsArmed attrib: Value
    
    Thanks to Itamar
    https://stackoverflow.com/questions/7905380/testing-equivalence-of-xml-etree-elementtree
    """
    if e1.tag != e2.tag:
        print('tag')
        print(e1)
        print(e2)
        print(e1.tag + ' != ' + e2.tag)
        return False
    if e1.text != e2.text:
        print('text')
        print(e1)
        print(e2)
        print(e1.text + ' != ' + e2.text)
        return False
    if e1.tail != e2.tail:
        print('tail')
        print(e1)
        print(e2)
        print(e1.tail + ' != ' + e2.tail)
        return False

    copy_e1_attrib = e1.attrib.copy()
    copy_e2_attrib = e2.attrib.copy()

    if e1.tag in IGNORE_ATTRIB_FOR:
        remove = IGNORE_ATTRIB_FOR[e1.tag]
        for key in remove:
            if key in copy_e1_attrib:
                del copy_e1_attrib[key]
            if key in copy_e2_attrib:
                del copy_e2_attrib[key]

    if copy_e1_attrib != copy_e2_attrib:
        print('attrib')
        print(e1)
        print(e2)
        print(str(copy_e1_attrib) + ' != ' + str(copy_e2_attrib))
        print('originally:')
        print(str(e1.attrib) + ', ' + str(e2.attrib))
        return False
    if len(e1) != len(e2):
        print('len')
        print(e1)
        print(e2)
        print(str(len(e1)) + ' != ' + str(len(e2)))
        return False

    # For send tracks, we only care about the intersection of the two track's send tracks
    # Ones that have been added on the track from branch will not be in base
    # Ones that have been removed no longer matter
    # These can be different as it is the set of return tracks that differ, when the track could
    # actually be no different
    # The IDs of the elements in Sends are not IDs of the tracks, they are only an ordering,
    # therefore currently we must also pass the return tracks into this function so that we
    # can calculate which sends actually intersect
    if e1.tag == 'Sends':
        if not e2.tag == 'Sends':
            return False
        relevant_send_results = []
        for ba_loc in send_map:
            br_loc = send_map[ba_loc]
            relevant_send_results.append(
                tree_equal(
                    get_elem_attr_value(e1, 'TrackSendHolder', 'Id', str(br_loc)), 
                    get_elem_attr_value(e2, 'TrackSendHolder', 'Id', str(ba_loc)),
                    send_map
                )
            )
        return all(relevant_send_results)

    return all(tree_equal(c1, c2, send_map) for c1, c2 in zip(e1, e2))
    
def get_elem_attr_value(elem, name, attrib, value):
    elems = elem.findall(name)
    for e in elems:
        if e.attrib[attrib] == value:
            return e

