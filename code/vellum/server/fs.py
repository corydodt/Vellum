import sys, os

from twisted.python import util

from vellum.util.filesystem import Filesystem

# for py2exe, make sure __file__ is real
if not os.path.isfile(__file__):
    __file__ = sys.executable


fs = Filesystem(os.getcwd())
fs.images = Filesystem(fs("images"), mkdir=1)
fs.party = Filesystem(fs("party"), mkdir=1)
fs.encounters = Filesystem(fs("encounters"), mkdir=1)
fs.aliases = Filesystem(fs("aliases"), mkdir=1)
fs.help = fs("help.txt")
