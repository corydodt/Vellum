import sys, os
# hack taken from <http://www.livejournal.com/users/glyf/7878.html>
import _winreg
def getGtkPath():
    subkey = 'Software/GTK/2.0/'.replace('/','\\')
    path = None
    for hkey in _winreg.HKEY_LOCAL_MACHINE, _winreg.HKEY_CURRENT_USER:
        reg = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, subkey)
        for vname in ("Path", "DllPath"):
            try:
                try:
                    path, val = _winreg.QueryValueEx(reg, vname)
                except WindowsError:
                    pass
                else:
                    return path
            finally:
                _winreg.CloseKey(reg)

path = getGtkPath()
if path is None:
    raise ImportError("Couldn't find GTK DLLs.")
os.environ['PATH'] += ';'+path.encode('utf8')


# win32all
try:
    from win32ui import CreateFileDialog
    import win32con
except:
    def CreateFileDialog(*args, **kwargs):
        """TODO - use gtk one"""

if sys.platform == 'win32':
    os.environ['SDL_VIDEODRIVER'] = 'windib'

def hwnd(window):
    if sys.platform == 'win32':
        return window.handle
    else:
        return window.xid

def sdlHack(widget, *args):
    """Slap a pygame (SDL) window inside a widget"""
    handle = hwnd(widget.window)
    # size = widget.size_request()
    # print size
    os.environ['SDL_WINDOWID'] = hex(handle)
    global pygame
    import pygame # do NOT do this before setting SDL_WINDOWID
    pygame.display.init()
    #pygame.display.set_mode(size)
    pygame.display.set_mode((200,200))

# end goddamn ugly gtk and pygame hacks
# end goddamn ugly gtk and pygame hacks
# end goddamn ugly gtk and pygame hacks

import gtk
from gtk import glade

from twisted.python import log

from vellum.server import PBPORT
from vellum.gui.fs import fs


class Icon:
    """
    - image: the image used for the icon
    - xy: a 2-tuple specify the top-left corner of the icon
    """
    def __init__(self):
        self.image = None
        self.xy = (None, None)

class Model:
    """
    - background: the image used as the background (usually, a map)
    - icons: a list of icon objects
    """
    def __init__(self, background):
        self.background = background
        self.icons = []


class FrontEnd:
    def __getattr__(self, name):
        if name.startswith("gw_"):
            return self.glade.get_widget(name[3:])
        raise AttributeError, "%s instance has no attribute %s" % (
            self.__class__, name)

    def __init__(self, deferred, netclient, fps):
        self.fps = fps
        self.deferred = deferred
        self.netclient = netclient

        self.glade = glade.XML(fs.gladefile)
        self.glade.signal_autoconnect(self)

        drawing = self.gw_drawingarea1
        drawing.connect('map-event', sdlHack)

        # coordinate and scale for displaying the model
        self.scale = 1.0
        self.corner = (0,0)

        # force size_allocate hook to get called
        self.gw_drawingarea1.queue_draw()


    def on_Tester_destroy(self, widget):
        log.msg("Goodbye.")
        self.deferred.callback(None)

    def on_drawingarea1_size_allocate(self, widget, rectangle):
        pygame.display.set_mode((rectangle.width, rectangle.height))

    def on_connect_button_clicked(self, widget):
        text = self.gw_server.get_child().get_text()
        d = self.netclient.startPb(text, PBPORT)
        d.addErrback(log.err)
        d.addCallback(self._cb_gotFileInfos)
        d.addCallback(lambda _: self.displayMap())

    def _getMapInfo(self):
        for fi in self.fileinfos:
            if fi['type'] == 'map':
                return fi


    def displayMap(self):
        mapinfo = self._getMapInfo()
        log.msg('displaying map %s' % (mapinfo['name'],))
        image_object = pygame.image.load(fs.downloads(mapinfo['name']))
        self.model = Model(image_object)
        self.view = View(self.model)
        # self.view.addCharacter
        # self.view.addItem
        # self.view.addText
        # self.view.addSound
        self.view.clearObscurement()
        # self.view.obscure?

    def _cb_gotFileInfos(self, fileinfos):
        self.fileinfos = fileinfos
