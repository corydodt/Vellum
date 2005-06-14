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
# my windows build of gnomecanvas uses a nonstandard name
try:
    from gnome import canvas as gnomecanvas
except ImportError:
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

class Operation:
    """A stateful activity involving the mouse and the user.
    An operation has:
    (- access buttons
     - access menu items
        These need to be toggled simultaneously when an operation is turned on
        or off.)
    - access keys
    - a rectangular area
    """
    def __init__(self, gui):
        self.echo_controls = [] # controls that need to be updated when on or
                                # off
        self.begin_x = None
        self.begin_y = None
        self.end_x = None
        self.end_y = None

        self.gui = gui

    def beginState(self):
        """Impl. in subclasses to do things when the button is pushed,
        including changing the cursor
        """
    def endState(self):
        """Impl. in subclasses to do things when the button is turned off,
        including changing the cursor
        """


    def beginAt(self, x, y):
        self.begin_x = x
        self.begin_y = y
        self.begin()
    def begin(self):
        pass

    def updateAt(self, x, y):
        self.update(x, y)
    def update(self, x, y):
        pass

    def endAt(self, x, y):
        self.end_x = x
        self.end_y = y
        self.finish()
    def finish(self):
        pass

class Pan(Operation):
    cursor = gdk.Cursor(gdk.DOT)
    begin_cursor = gdk.Cursor(gdk.CIRCLE)
    def beginState(self):
        self.gui.canvas.window.set_cursor(self.cursor)
    def endState(self):
        self.gui.canvas.window.set_cursor(None)
    def begin(self):
        self.gui.canvas.window.set_cursor(self.begin_cursor)
    def finish(self):
        self.gui.canvas.window.set_cursor(self.cursor)

    def update(self, x, y):
        ha = self.gui.canvas.get_hadjustment()
        va = self.gui.canvas.get_vadjustment()

        # FIXME - Pan could be much faster, but it gets jittery
        x_moved = self.begin_x - x
        y_moved = self.begin_y - y
        
        alloc = self.gui.canvas.get_allocation()

        if x_moved:
            if ha.lower <= (ha.value + x_moved + alloc.width) <= ha.upper:
                ha.set_value(ha.value + x_moved)
            elif ha.value + x_moved + alloc.width > ha.upper:
                ha.set_value(ha.upper - alloc.width)
            elif ha.lower < ha.value + x_moved + alloc.width:
                ha.set_value(ha.lower)

        if y_moved:
            if va.lower <= (va.value + y_moved + alloc.height) <= va.upper:
                va.set_value(va.value + y_moved)
            elif va.value + y_moved + alloc.height > va.upper:
                va.set_value(va.upper - alloc.height)
            elif va.lower < va.value + y_moved + alloc.height:
                va.set_value(va.lower)


class Paint(Operation):
    pass


class Magnify(Operation):
    cursor = gdk.Cursor(gdk.TARGET)
    def beginState(self):
        self.gui.canvas.window.set_cursor(self.cursor)
    def endState(self):
        self.gui.canvas.window.set_cursor(None)
    def begin(self):
        self.drawn = None

    def finish(self):
        """Zoom so the inscribed area is maximized in the main window"""
        if self.drawn:
            x1 = self.drawn.get_property('x1')
            y1 = self.drawn.get_property('y1')
            x2 = self.drawn.get_property('x2')
            y2 = self.drawn.get_property('y2')

            self.drawn.destroy()
            self.drawn = None

            canvas = self.gui.canvas

            # baseline measurements
            alloc = canvas.get_allocation()
            box_w = abs(x2 - x1)
            box_h = abs(y2 - y1)

            ratio_w = alloc.width / box_w
            ratio_h = alloc.height / box_h

            # calculate zoom - the smaller of the two scaling ratios
            last_zoom = 10.0 / canvas.c2w(10, 10)[0]
            if ratio_w < ratio_h:
                zoom = ratio_w
            else:
                zoom = ratio_h
            if zoom > 8:
                zoom = last_zoom 

            # scale canvas
            canvas.set_pixels_per_unit(zoom)

            # remap coordinates
            box_w, box_h, x1, y1, x2, y2 = (
                    [pt/last_zoom * zoom for pt in (box_w, box_h, x1,y1,x2,y2)])

            # get the NW corner of the selection rectangle for scroll adjust
            if x1 < x2: west = x1
            if y1 < y2: north = y1

            # center scrollbars on inscribed area
            if ratio_w < ratio_h:
                x_offset = west
                y_offset = north - (alloc.height - box_h) / 2
            else:
                x_offset = west - (alloc.width - box_w) / 2
                y_offset = north

            ha = canvas.get_hadjustment()
            ha.set_value(x_offset)
            va = canvas.get_vadjustment()
            va.set_value(y_offset)


    def update(self, x, y):
        if self.drawn:
            self.drawn.destroy()
        x, y = self.gui.canvas.c2w(x, y)
        bx, by = self.gui.canvas.c2w(self.begin_x, self.begin_y)

        root = self.gui.canvas.root()
        self.drawn = root.add("GnomeCanvasRect", x1=bx,
                              y1=by,
                              x2=x, y2=y,
                              width_pixels=1,
                              # outline_stipple = wtf?
                              outline_color="gray")
        self.drawn.show()



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
        self.gw_viewport1.modify_bg(gtk.STATE_NORMAL, gdk.Color(0xff0000))
        # now modify the new style object
        self.gw_viewport1.style.bg_pixmap[gtk.STATE_NORMAL] = _pixmap

        self.canvas = None

        # these used to remember the last view of the model between sessions
        self.scale = 1.0
        self.corner = (0,0)

        self.model = None
        self.tool_active = None
        self.active_operation = None

        # stateful operations that have mouse interactivity
        self.operations = {
            'pan_on': Pan,
            'paint_on': Paint,
            'magnify_on': Magnify,
            }

        self._mousedown = 0

    def on_quit_active(self, widget):
        self.quit()


    def on_toolbar_toggled(self, widget):
        """Toggle off any button which is clicked while on.
        Otherwise there's always one button that's "on".
        """
        if widget.get_active():
            tool_changed = (self.tool_active != widget.name)

            # cancel active operation if tool has changed
            if self.active_operation and tool_changed:
                self.active_operation.endState()

            # turn off other tools
            for child in self.gw_toolbar1.get_children():
                if child is not widget:
                    child.set_active(False)

            self.tool_active = widget.name
            self.active_operation = self.operations[self.tool_active](self)
            self.active_operation.beginState()
        else:
            self.tool_active = None
            if self.active_operation:
                self.active_operation.endState()

    def on_zoom100pct_activate(self, widget):
        if self.canvas:
            self.canvas.set_pixels_per_unit(1.0)

    def on_zoomfit_activate(self, widget):
        if self.canvas:
            print 'TODO: fit'


    def on_Vellum_destroy(self, widget):
        self.quit()

    def quit(self):
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

    def beginOperation(self, opname, x, y):
        self._mousedown = 1
        self.active_operation.beginAt(x,y)

    def updateOperation(self, opname, x, y):
        self.active_operation.updateAt(x, y)

    def finishOperation(self, opname, x, y):
        self._mousedown = 0
        self.active_operation.endAt(x, y)

    def on_canvas_button_press_event(self, widget, ev):
        if self.tool_active:
            self.beginOperation(self.tool_active, ev.x, ev.y)

    def on_canvas_button_release_event(self, widget, ev):
        if self.active_operation:
            assert self._mousedown
            self.finishOperation(self.tool_active, ev.x, ev.y)

    def on_canvas_motion_notify_event(self, widget, ev):
        if self._mousedown:
            self.updateOperation(self.tool_active, ev.x, ev.y)

    def displayModel(self):
        if self.canvas is None:
            self.canvas = gnomecanvas.Canvas()
            # make canvas draw widgets in the NW corner...
            self.canvas.set_center_scroll_region(False)

            # out with the old
            self.gw_viewport1.destroy()
            # in with the new
            self.gw_scrolledwindow1.add(self.canvas)
            self.canvas.show()

            self.canvas.connect('button-press-event',
                    self.on_canvas_button_press_event)
            self.canvas.connect('button-release-event',
                    self.on_canvas_button_release_event)
            self.canvas.connect('motion-notify-event',
                    self.on_canvas_motion_notify_event)

        # TODO - clear canvas for a new map

        mapinfo = self._getMapInfo()
        log.msg('displaying map %s' % (mapinfo['name'],))
        self.bg = gdk.pixbuf_new_from_file(fs.downloads(mapinfo['name']))
        self.model = Model(self.bg)
        root = self.canvas.root()
        root.add("GnomeCanvasPixbuf", pixbuf=self.bg)
        self.canvas.set_scroll_region(0, 0, 
                                      self.bg.get_width(),
                                      self.bg.get_height()
                                      )

                 
        for n, character in enumerate(self._getCharacterInfo()):
            icon_image = gdk.pixbuf_new_from_file(
                                fs.downloads(character['name'])
                                                  )
            icon = Icon()
            self.model.icons.append(icon)
            icon.image = icon_image
            if character['corner'] is not None:
                icon.xy = character['corner']
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
