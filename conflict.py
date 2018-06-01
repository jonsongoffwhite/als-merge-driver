import xml.etree.ElementTree as ET
import json
import os

class Conflict():

    def __init__(self, base, ours, theirs):
        self.base = base
        self.ours = ours
        self.theirs = theirs

    def write(self, folder, filename):
        data = {
            "base": self.base,
            "ours": self.ours,
            "theirs": self.theirs,
        }

        if not os.path.exists(folder):
            os.makedirs(folder)

        with open(folder+'/'+filename, 'w') as f:
            json.dump(data, f)

        with open('done', 'w') as f:
            pass
