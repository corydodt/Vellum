import os

from nevow import athena

import webby

webbyPkg = athena.AutoJSPackage(os.path.dirname(webby.__file__))
