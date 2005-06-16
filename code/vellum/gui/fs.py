import sys, os

from twisted.python import util

from vellum.util.filesystem import Filesystem

# for py2exe, make sure __file__ is real
if not os.path.isfile(__file__):
    __file__ = sys.executable


fs = Filesystem(util.sibpath(sys.argv[0], ''))
fs.downloads = fs.new("downloads", mkdir=1)
fs.gladefile = fs("vellum.glade")
fs.background = fs("pixmaps", "slatebg.png")
