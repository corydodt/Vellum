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

        # remap coordinates post-zoom
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

        self._drawDefaultBackground()

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

    def _drawDefaultBackground(self):
        # allocate the slate background
        self.bg = gdk.pixbuf_new_from_file(fs.background)
        # create a pixmap to put a tile into
        _pixmap = gdk.Pixmap(self['viewport1'].window, 
                             self.bg.get_width(),
                             self.bg.get_height())
        gc = _pixmap.new_gc()
        _pixmap.draw_pixbuf(gc, self.bg, 0, 0, 0, 0)
        # a kludge to make gw_viewport1 generate a new style object:
        self['viewport1'].modify_bg(gtk.STATE_NORMAL, gdk.Color(0xff0000))
        # now modify the new style object
        self['viewport1'].style.bg_pixmap[gtk.STATE_NORMAL] = _pixmap


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
        """Hook a new icon up to an observer"""
        for icon in new:
            if getattr(icon, 'controller', None) is not self:
                icon.registerObserver(self)
        # TODO - raise obscurement to the top

    def property_iconname_change_notification(self, icon, old, new):
        icon.iconimage = gdk.pixbuf_new_from_file(fs.downloads(new))

    def property_iconimage_change_notification(self, icon, old, new):
        canvas = self.view['canvas']
        root = canvas.root()
        image = icon.iconimage
        corner = icon.iconcorner
        if corner is None: corner = (0,0)
        x, y = corner
        if icon.widget is None:
            igroup = root.add("GnomeCanvasGroup", x=x, y=y)
            igroup.add("GnomeCanvasPixbuf",
                     pixbuf=image,
                     x=0, y=0)
            fontgroup = igroup.add("GnomeCanvasGroup",
                                   x=image.get_width() /2,
                                   y=image.get_height() + 3
                                   )
            # outline
            text = fontgroup.add("GnomeCanvasText",
                                 font="verdana bold",
                                 text=icon.iconname,
                                 )
            w = text.get_property('text-width')
            h = text.get_property('text-height')
            textbg = fontgroup.add("GnomeCanvasRect",
                          fill_color = "white",
                          x1=-3*w/4, y1=-3*h/4,
                          x2=3*w/4, y2=3*h/4,
                          )
            textbg.lower_to_bottom()

            fontgroup.lower_to_bottom()

            igroup.connect('event', self.on_icon_event, icon)
            icon.widget = igroup

    def property_iconsize_change_notification(self, icon, old, new):
        w = icon.iconimage.get_width()
        h = icon.iconimage.get_height()
        scale_ratio = icon.iconsize*(100/w) / self.map.scale100px
        w = w*scale_ratio
        h = h*scale_ratio
        # FIXME - this loses the original image scale, so repeatedly
        # FIXME   scaling to this size will make the object grow or shrink
        # FIXME   geometrically instead of remaining the same size.
        image = icon.iconimage.scale_simple(w,h,gdk.INTERP_HYPER)
        # redraw a new, resized icon over the old one
        icon.widget.destroy()
        icon.widget = None
        icon.iconimage = image

    def property_iconcorner_change_notification(self, icon, old, new):
        x, y = new
        if old is None: old = (0,0)
        ox, oy = old
        icon.widget.move(x-ox, y-oy)


    def on_icon_event(self, widget, event, icon):
        type = event.type.value_name.lower()
        handler = getattr(self, 'on_icon_%s' % (type,), None)
        if handler is not None:
            return handler(widget, event, icon)

    def on_icon_gdk_enter_notify(self, widget, event, icon):
        pass # highlight or something

    def on_icon_gdk_leave_notify(self, widget, event, icon):
        pass # unhighlight or something

    def on_icon_gdk_button_press(self, widget, event, icon):
        icon.grabbed = True

    def on_icon_gdk_button_release(self, widget, event, icon):
        icon.selected = not icon.selected
        icon.grabbed = False

    def on_icon_gdk_motion_notify(self, widget, event, icon):
        if icon.grabbed:
            iw, ih = icon.iconimage.get_width(), icon.iconimage.get_height()
            self.map.moveIcon(icon, event.x - iw/2, event.y - ih/2)

    def property_scale100px_change_notification(self, model, old, new):
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
        # TODO - delete old obscurement?
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
        pass
    def on_canvas_button_release_event(self, widget, ev):
        pass
    def on_canvas_motion_notify_event(self, widget, ev):
        pass
