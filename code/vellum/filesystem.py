import sys, os

from twisted.python import util

class Filesystem:
    def __init__(self, path, mkdir=0):
        if mkdir:
            try:
                os.makedirs(path)
            except EnvironmentError:
                pass
        self.path = os.path.abspath(path)

    def __call__(self, *paths):
        return os.path.join(self.path, *paths)

# for py2exe, make sure __file__ is real
if not os.path.isfile(__file__):
    __file__ = sys.executable


fs = Filesystem(util.sibpath(__file__, ''))
fs.downloads = Filesystem(fs("downloads"), mkdir=1)
fs.gladefile = fs("vellum.glade")
