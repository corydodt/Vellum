import sys, os

from twisted.python import util

from vellum.util.filesystem import Filesystem

# for py2exe, make sure __file__ is real
if not os.path.isfile(__file__):
    __file__ = sys.executable


fs = Filesystem(os.getcwd())
fs.images = fs.new("images", mkdir=1)
fs.party = fs.new("party", mkdir=1)
fs.encounters = fs.new("encounters", mkdir=1)
fs.aliases = fs.new("aliases", mkdir=1)
fs.help = fs("help.txt")
fs.maps = fs.new("maps", mkdir=1)
