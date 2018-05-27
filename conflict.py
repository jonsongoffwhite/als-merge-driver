import xml.etree.ElementTree as ET

class Conflict():

    def __init__(self, base, ours, theirs):
        self.base = base
        self.ours = ours
        self.theirs = theirs
