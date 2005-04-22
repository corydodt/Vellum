import os

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

