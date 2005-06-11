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

# end goddamn ugly gtk hack
# end goddamn ugly gtk hack
# end goddamn ugly gtk hack

import gtk
from gtk import glade, gdk
import gnomecanvas

from twisted.python import log
from twisted.internet import task, reactor

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

        # allocate the slate background
        self.bg = gdk.pixbuf_new_from_file(fs.background)
        # create a pixmap to put a tile into
        _pixmap = gdk.Pixmap(self.gw_viewport1.window, 
                             self.bg.get_width(),
                             self.bg.get_height())
        gc = _pixmap.new_gc()
        _pixmap.draw_pixbuf(gc, self.bg, 0, 0, 0, 0)
        # a kludge to make gw_viewport1 generate a new style object:
        self.gw_viewport1.modify_bg(gtk.STATE_NORMAL, gdk.Color(0))
        # now modify the new style object
        self.gw_viewport1.style.bg_pixmap[gtk.STATE_NORMAL] = _pixmap

        self.canvas = None

        # these used to remember the last view of the model between sessions
        self.scale = 1.0
        self.corner = (0,0)

        self.model = None




    def on_Tester_destroy(self, widget):
        log.msg("Goodbye.")
        self.deferred.callback(None)

    def on_connect_button_clicked(self, widget):
        text = self.gw_server.get_child().get_text()
        d = self.netclient.startPb(text, PBPORT)
        d.addErrback(log.err)
        d.addCallback(self._cb_gotFileInfos)
        d.addCallback(lambda _: self.displayModel())

    def _getMapInfo(self):
        for fi in self.fileinfos:
            if fi['type'] == 'map':
                return fi

    def _getCharacterInfo(self):
        for fi in self.fileinfos:
            if fi['type'] == 'character':
                yield fi

    def displayModel(self):
        if self.canvas is None:
            self.canvas = gnomecanvas.Canvas()
            # make canvas draw widgets in the NW corner...
            self.canvas.set_center_scroll_region(False)
            self.gw_viewport1.add(self.canvas)
            self.canvas.show()

        # TODO - clear canvas for a new map

        mapinfo = self._getMapInfo()
        log.msg('displaying map %s' % (mapinfo['name'],))
        self.bg = gdk.pixbuf_new_from_file(fs.downloads(mapinfo['name']))
        self.model = Model(self.bg)
        root = self.canvas.root()
        root.add("GnomeCanvasPixbuf", pixbuf=self.bg)
        self.canvas.set_size_request(self.bg.get_width(),
                                     self.bg.get_height()
                                     )
                 
        for n, character in enumerate(self._getCharacterInfo()):
            icon_image = gdk.pixbuf_new_from_file(
                                fs.downloads(character['name'])
                                                  )
            icon = Icon()
            self.model.icons.append(icon)
            icon.image = icon_image
            icon.xy = n*80, n*80
            self.canvas.root().add("GnomeCanvasPixbuf", 
                                   pixbuf=icon.image,
                                   x=icon.xy[0],
                                   y=icon.xy[1],
                                   )
        # self.addCharacter
        # self.addItem
        # self.addText
        # self.addSound
        # self.clearObscurement()
        # self.obscure?

    def _cb_gotFileInfos(self, fileinfos):
        self.fileinfos = fileinfos
