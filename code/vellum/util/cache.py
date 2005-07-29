"""A cache management framework"""

import os
try:
    from cPickle import load, dump
except ImportError:
    from pickle import load, dump

from md5 import md5

class Cache:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        try:
            os.makedirs(root)
        except EnvironmentError:
            pass
        self.idxpath = os.path.join(root, 'idx')
        f = file(self.idxpath, 'ab+')
        try:
            self.idx = load(f)
        except EOFError:
            self.idx = {}

    def __contains__(self, uri):
        return uri in self.idx 

    def _writeIndex(self):
        f = file(self.idxpath, 'wb')
        dump(self.idx, f, 2)

    def lookup(self, uri):
        """Return the filename of the cache file representing the uri"""
        return os.path.join(self.idxpath, self.idx[uri])

    def read(self, uri):
        """Return the data of the cache file that was downloaded from the uri"""
        return file(os.path.join(self.idxpath, self.idx[uri]), 'rb').read()

    def remove(self, uri):
        """Remove the file keyed at uri"""
        del self.idx[uri]
        os.path.unlink(uri)
        self._writeIndex()

    def reserve(self, uri):
        """Return a filename to be used by something else that will write a
        file into the cache
        """
        digest = md5(uri).hexdigest()
        self.idx[uri] = os.path.join(self.root, digest)
        self._writeIndex()
        return self.idx[uri]

    def store(self, data, uri):
        """Write data to a cache file and store it with the uri as the key"""
        digest = md5(uri).hexdigest()
        new = os.path.join(self.root, digest)
        newfile = file(new, 'wb')
        newfile.write(data)
        newfile.close()
        self.idx[uri] = new
        self._writeIndex()
