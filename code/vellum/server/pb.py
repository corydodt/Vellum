"""The PB service of the vellum server."""
import ConfigParser

from twisted.spread import pb

import yaml

class Gameness(pb.Root):
    """PLEASE BE CAREFUL.
    Removing any of the remote_ methods here, or changing any of their return
    values, will result in incompatible network changes.  Be aware of that and
    try to minimize incompatible network changes.

    At some point in the future, there will be a policy about what changes are
    allowed in what versions.
    """
    def __init__(self):
        cp = ConfigParser.ConfigParser()
        cp.read('vellumpb.ini')
        self.lastmap = cp.get('vellumpb', 'lastmap', None)

    def remote_listAvailableFiles(self):
        return yaml.loadFile(self.lastmap).next()

