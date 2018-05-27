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

    
}

IGNORE_ALWAYS = {
}

def tree_equal(e1, e2):
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
    return all(tree_equal(c1, c2) for c1, c2 in zip(e1, e2))
    
