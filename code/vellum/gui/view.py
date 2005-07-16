from __future__ import division

import sys, os
# hack taken from <http://www.livejournal.com/users/glyf/7878.html>
def getGtkPath():
    import _winreg
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

if sys.platform == 'win32':
    path = getGtkPath()
    if path is None:
        raise ImportError("Couldn't find GTK DLLs.")
    os.environ['PATH'] += ';'+path.encode('utf8')

## end damn gtk hack

import gtk
from gtk import gdk


from twisted.python import log
from twisted.internet import reactor

# my windows build of gnomecanvas uses a nonstandard name
try:
    from gnome import canvas as gnomecanvas
except ImportError:
    import gnomecanvas

from gtkmvc import view

from vellum.gui.ctlutil import SilentController
from vellum.gui.fs import fs


class ZoomCanvas(gnomecanvas.Canvas):
    """Canvas with methods for zooming on a particular area"""
    def zoomBox(self, x1, y1, x2, y2):
        """Zoom to fit and center on the world coordinates given"""
        # baseline measurements
        alloc = self.get_allocation()
        box_w = abs(x2 - x1)
        box_h = abs(y2 - y1)

        ratio_w = alloc.width / box_w
        ratio_h = alloc.height / box_h

        # calculate zoom - the smaller of the two scaling ratios
        zoom = min([ratio_w, ratio_h])
        # set a reasonable max for scale degree - 800%
        last_zoom = 10.0 / self.c2w(10, 10)[0]
        if zoom > 8:
            zoom = last_zoom 

        # scale the main canvas
        self.set_pixels_per_unit(zoom)

        # remap coordinates
        o1_to_o2 = lambda *pts: [pt * zoom  for pt in pts]
        box_w, box_h, x1, y1, x2, y2 = o1_to_o2(box_w, box_h, x1,y1,x2,y2)

        # get the NW corner of the selection rectangle for scroll adjust
        if x1 < x2: west = x1
        else: west = x2
        if y1 < y2: north = y1
        else: north = y2

        # center scrollbars on inscribed area
        if ratio_w < ratio_h:
            x_offset = west
            y_offset = north - (alloc.height - box_h) / 2
        else:
            x_offset = west - (alloc.width - box_w) / 2
            y_offset = north

        ha = self.get_hadjustment()
        ha.set_value(x_offset)
        va = self.get_vadjustment()
        va.set_value(y_offset)


class BigView(view.View):
    """All the widgets down to the main map window"""
    def __init__(self, controller):
        view.View.__init__(self, controller, fs.gladefile, "Vellum")
        # graphics setup
        self['Vellum'].set_icon_from_file(fs('pixmaps', 'v.ico'))

        # set one button icon that isn't stock
        _hand_pb = gdk.pixbuf_new_from_file(fs('pixmaps', 'stock_stop.png'))
        _image = gtk.Image()
        _image.set_from_pixbuf(_hand_pb)
        _image.show()
        self['pan_on'].set_icon_widget(_image)

        self.controller = controller

    def landCanvas(self):
        """Put in a canvas"""
        if self['viewport1'] is None:
            return
        self['viewport1'].destroy()

        canvas = ZoomCanvas()
        canvas.set_center_scroll_region(False)


        self['scrolledwindow1'].add(canvas)
        canvas.show()
        self['canvas'] = canvas

        c = self.controller
        canvas.connect('button-press-event', 
                       c.on_canvas_button_press_event)
        canvas.connect('button-release-event', 
                       c.on_canvas_button_release_event)
        canvas.connect('motion-notify-event', 
                       c.on_canvas_motion_notify_event)


class BigController(SilentController):
    def __init__(self, map, netmodel, deferred):
        self.deferred = deferred
        self.netmodel = netmodel
        self.map = map
        # this is kind of a kludge.  I don't think I'm "supposed" to register
        # a controller with two models, and the initializer only accepts one.
        # It doesn't seem to do anything but set self.model, so I just picked
        # one arbitrarily.
        map.registerObserver(self)
        netmodel.registerObserver(self)
        SilentController.__init__(self, map)

        self.justloaded = 0

    def property_mapname_change_notification(self, model, old, new):
        self.map.image = gdk.pixbuf_new_from_file(fs.downloads(new))
        obsc = '%s (obscurement)' % (new,)
        self.map.obscurement = gdk.pixbuf_new_from_file(fs.downloads(obsc))
        self.view['Vellum'].set_title('Vellum - %s' % (new,))
        log.msg('displaying map %s' % (new,))

    def property_icons_change_notification(self, model, old, new):
        root = self.view['canvas'].root()
        for icon in new:
            if self.map.icons[icon] is not None:
                icon_image = gdk.pixbuf_new_from_file(
                                    fs.downloads(icon.iconname)
                                                      )
                x, y = self.map.icons[icon]
                igroup = root.add("GnomeCanvasGroup", 
                         x=x, y=y
                         )
                igroup.add("GnomeCanvasPixbuf",
                         pixbuf=icon_image,
                         x=0, y=0)
                igroup.add("GnomeCanvasText",
                        text=icon.iconname,
                        x=icon_image.get_width() / 2,
                        y=icon_image.get_height() + 3)

    def property_scale_change_notification(self, model, old, new):
        print 'map scale changed'
    def property_image_change_notification(self, model, old, new):
        # put in the view window which is invisible by default
        self.view.landCanvas()
        root = self.view['canvas'].root()
        root.add("GnomeCanvasPixbuf", pixbuf=new)
        self.view['canvas'].set_scroll_region(0, 0, 
                                              new.get_width(),
                                              new.get_height()
                                              )
        # turn on buttons now that canvas is active
        self.view['magnify_on'].set_sensitive(True)
        self.view['paint_on'].set_sensitive(True)
        self.view['pan_on'].set_sensitive(True)

        # set a flag so map initialization can happen later
        self.justloaded = 1

    def property_laser_change_notification(self, model, old, new):
        print 'laser moved'
    def property_attention_change_notification(self, model, old, new):
        print 'new attention rectangle'
    def property_target_lines_change_notification(self, model, old, new):
        print 'target lines changed'
    def property_follow_lines_change_notification(self, model, old, new):
        print 'follow lines changed'
    def property_drawings_change_notification(self, model, old, new):
        print 'drawings added or removed'
    def property_notes_change_notification(self, model, old, new):
        print 'notes added or removed'
    def property_lastwindow_change_notification(self, model, old, new):
        # restore the most recent view of this map the first time it loads
        if self.justloaded:
            # call after the widget has been configured
            reactor.callLater(0.1, 
                              self.view['canvas'].zoomBox, *model.lastwindow)
            self.justloaded = 0
    def property_obscurement_change_notification(self, model, old, new):
        root = self.view['canvas'].root()
        root.add("GnomeCanvasPixbuf", pixbuf=new)


    def on_quit_activate(self, widget):
        self.quit()

    def on_Vellum_destroy(self, widget):
        self.quit()

    def quit(self):
        log.msg("Goodbye.")
        self.deferred.callback(None)

    def on_connect_button_clicked(self, widget):
        self.netmodel.server = self.view['server'].get_child().get_text()

    def on_canvas_button_press_event(self, widget, ev):
        print 'canvas button pr'
    def on_canvas_button_release_event(self, widget, ev):
        print 'canvas button rel'
    def on_canvas_motion_notify_event(self, widget, ev):
        pass
