import os

from nevow import athena

from webby import RESOURCE

webbyPkg = athena.AutoJSPackage(RESOURCE('static'))
