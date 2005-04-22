import sys, os

from twisted.python import util

from vellum.utilfilesystem import Filesystem

# for py2exe, make sure __file__ is real
if not os.path.isfile(__file__):
    __file__ = sys.executable


fs = filesystem.Filesystem(util.sibpath(sys.argv[0], ''))
fs.downloads = Filesystem(fs("downloads"), mkdir=1)
fs.gladefile = fs("vellum.glade")
