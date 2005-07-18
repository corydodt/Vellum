"""Models of stuff"""

from gtkmvc import model

import traceback
import re

class Icon(model.Model):
    __properties__ = {
        'iconname': 'x',
        'iconimage': None,
        'iconsize': '2.5ft',
        'iconcorner': None,
        }

    def __init__(self, *args, **kwargs):
        model.Model.__init__(self, *args, **kwargs)
        self.selected = False
        self.grabbed = False
        self.widget = None


class Map(model.Model,):
    __properties__ = {
        # these are managed with simple assignments
        'mapname': None,  # changing updates the string in the titlebar
        'image': None, # changing loads a new map background image
        'scale': '5ft', # physical units per 100px
        'obscurement': None,  # the gnomecanvaspixbuf of the obscurement
        'attention': (0,0,100,100),
        'lastwindow': (0,0,100,100),
        'laser': (0,0),
        # these require management methods
        'icons': {},  # {icon object: x, y}
        'target_lines': [], # specifies two icons (from, to) for a target arrow
        'follow_lines': [], # specifies two icons (from, to) for a follow arrow
        'drawings': {},
        'notes': {},
        }
    def moveIcon(self, icon, x, y):
        self.icons[icon] = (x, y)
        icon.iconcorner = (x,y)
    def delIcon(self, icon):
        del self.icons[icon]
        self.icons = self.icons
    def addIcon(self, name, size, ):
        """Add the icon to the model
        Follow with .moveIcon if you want to place the icon on the map
        """
        icon = Icon()
        self.icons[icon] = None
        self.icons = self.icons
        icon.iconname = name
        icon.size = size
        return icon

    def delTarget(self, left, right):
        if (left, right) in self.target_lines:
            self.target_lines.remove((left, right))
            self.target_lines = self.target_lines
    def addTarget(self, left, right):
        if (left, right) not in self.target_lines:
            self.target_lines.append((left, right))
            self.target_lines = self.target_lines

    def delFollow(self, left, right):
        if (left, right) in self.follow_lines:
            self.follow_lines.remove((left, right))
            self.follow_lines = self.follow_lines
    def addFollow(self, left, right):
        if (left, right) not in self.follow_lines:
            self.follow_lines.append((left, right))
            self.follow_lines = self.follow_lines
