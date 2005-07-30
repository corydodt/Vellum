"""Models of stuff"""

import traceback
import re

from gtkmvc import model
import yaml

from vellum.util.uuid import uuid
from vellum.util import cache, distance

class IDableModel(model.Model):
    def describeToYaml(self):
        assert None, 'better implement me in a subclass'

    def loadFromYamlString(self, data):
        assert None, 'better implement me in a subclass'


class Icon(IDableModel):
    __properties__ = {
        'iconname': 'x',
        'iconsize': 0.500, # physical units in meters
        'iconcorner': None,
        'iconuri': None,
        }

    def __init__(self):
        IDableModel.__init__(self)
        self.selected = False
        self.grabbed = False
        self.widget = None

    def dictify(self):
        dn = {}
        dn['name'] = self.iconname
        dn['type'] = 'character'
        dn['id'] = self.id
        dn['corner'] = self.iconcorner
        dn['size'] = '%sm' % (self.iconsize,)
        dn['uri'] = self.iconuri
        return dn



class Map(IDableModel):
    __properties__ = {
        # these are managed with simple assignments
        'mapname': None,  # changing updates the string in the titlebar
        'scale100px': 1.0, # physical units in meters per 100px
        'lastwindow': (0,0,100,100),
        'mapuri': None,
        # these are transient
        'laser': None,
        'attention': (0,0,100,100),
        # these require management methods
        'mapicon_added': None,
        'mapicon_removed': None,
        }

    def __init__(self):
        IDableModel.__init__(self, )
        self.icons = []
        self.target_lines = [] # specifies two icons (from, to) for an arrow
        self.follow_lines = [] # specifies two icons (from, to) for an arrow
        self.drawings = []
        self.notes = []
        self.sounds = []

    def describeToYaml(self):
        return yaml.dump(self.dictify())

    def dictify(self):
        dn = {}
        dn['name'] = self.mapname
        dn['id'] = self.id
        dn['files'] = []
        dn['files'].append(dict(type='background', 
                                uri=self.mapuri,
                                view=self.lastwindow,
                                scale100px='%sm' % (self.scale100px,),
                                )
                           )
        for icon in self.icons:
            dn['files'].append(icon.dictify())
        # obscurement
        # for.. dn['files']['drawings']
        # for.. dn['files']['sounds']
        # for.. dn['files']['notes']
        return dn

    def iterUris(self):
        """Return a generator for all URIs reachable from the map"""
        yield self.mapuri
        for icon in self.icons:
            yield icon.iconuri
        for note in self.notes:
            if note.noteuri:
                yield note.noteuri
        for sound in self.sounds:
            yield sound.sounduri
        for drawing in self.drawings:
            yield drawing.drawinguri

    def loadFromYaml(cls, data):
        """Load from data, a yaml file"""
        dn = yaml.load(data).next()
        map = Map()
        map.id = dn['id']
        map.mapname = dn['name']
        for file in dn['files']:
            if file['type'] == 'background':
                map.mapuri = file['uri']
                map.lastwindow = file['view']
                map.scale100px = distance.normalize(file['scale100px'])
            elif file['type'] == 'character':
                size = distance.normalize(file['size'])
                icon = map.addIcon(file['name'], size, file['id'])
                icon.iconuri = file['uri']
                if file['corner'] is not None:
                    map.moveIcon(icon, *file['corner'])
            # elif file['type'] == 'mask/obscurement'
            # elif file['type'] == 'drawing'
            # elif file['type'] == 'note'
            # elif file['type'] == 'sound'
            else:
                print 'Unhandled type: %s' % (file['type'],)
        return map
    #@
    loadFromYaml = classmethod(loadFromYaml)

    def loadFromYamlString(self, data):
        assert None, 'better implement me in a subclass'

    def iconFromId(self, iconid):
        for i in self.icons:
            if i.id == iconid: return i

    def moveIcon(self, icon, x, y):
        icon.iconcorner = (x,y)
    def delIcon(self, icon):
        self.icons.remove(icon)
        self.mapicon_remove = icon
    def addIcon(self, name, size, id):
        """Add the icon to the model
        Follow with .moveIcon if you want to place the icon on the map
        """
        icon = Icon()
        icon.id = id
        self.mapicon_added = icon
        self.icons.append(icon)
        icon.iconname = name
        icon.iconsize = size
        return icon
