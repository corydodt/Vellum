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

from vellum.util.ctlutil import SilentController
from vellum.gui.fs import fs, cache


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

def fileToImage(filename):
    """Return a visible gtk.Image from the filename"""
    pbuf = gdk.pixbuf_new_from_file(filename)
    image = gtk.Image()
    image.set_from_pixbuf(pbuf)
    image.show()
    return image


class BigView(view.View):
    """All the widgets down to the main map window"""
    def __init__(self, controller):
        view.View.__init__(self, controller, fs.gladefile, ["Preferences", 
                                                            "Vellum"])
        # graphics setup
        self['Vellum'].set_icon_from_file(fs('pixmaps', 'v.ico'))

        # set non-stock button icons
        hand = fileToImage(fs('pixmaps', 'stock_stop@24.png'))
        self['pan_on'].set_icon_widget(hand)
        laser = fileToImage(fs('pixmaps', 'laser_screen@24.png'))
        self['laser_on'].set_icon_widget(laser)


        self.controller = controller

        self._drawDefaultBackground()
        self['laser'] = None

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

    def cleanCanvas(self):
        if self['canvas'] is not None:
            self['canvas'].destroy()
            self['canvas'] = None
            # TODO - put viewport1 back

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
    def __init__(self, netmodel, deferred):
        self.deferred = deferred
        self.netmodel = netmodel
        netmodel.registerObserver(self)
        SilentController.__init__(self, netmodel)

        self.justloaded = 0

    def property_map_change_notification(self, model, old, map):
        map.registerObserver(self)
        for icon in map.icons:
            icon.registerObserver(self)
        # TODO - notes, drawings, sounds
        self.map = map 

    def property_mapuri_change_notification(self, model, old, new):
        file_loc = cache.lookup(new)
        self.map.image = gdk.pixbuf_new_from_file(file_loc)
        log.msg('displaying map %s' % (new,))
        if new is None:
            self.view.cleanCanvas()
            return
        # put in the view window which is invisible by default
        self.view.landCanvas()
        root = self.view['canvas'].root()
        img = self.map.image
        root.add("GnomeCanvasPixbuf", pixbuf=img)
        self.view['canvas'].set_scroll_region(0, 0, 
                                              img.get_width(),
                                              img.get_height()
                                              )
        # turn on buttons now that canvas is active
        self.view['magnify_on'].set_sensitive(True)
        self.view['paint_on'].set_sensitive(True)
        self.view['pan_on'].set_sensitive(True)
        self.view['laser_on'].set_sensitive(True)

        # set a flag so map initialization can happen later
        self.justloaded = 1

    def on_Preferences_delete_event(self, w, ev):
        w.hide()
        return True # don't call the default handler (w won't be destroyed)

    def on_username_focus_out_event(self, widget, event):
        self.netmodel.username = widget.get_text()

    def property_recent_servers_change_notification(self, model, old, new):
        set_model_from_list(self.view['server'], new)
        model.saveIni()

    def property_username_change_notification(self, model, old, new):
        self.view['username'].set_text(new)
        status = self.view['statusbar1']
        ctx = status.get_context_id('property_username_change_notification')
        status.pop(ctx)
        status.push(ctx, 'Username %s' % (new,))
        if old != new:
            model.saveIni()

    def property_mapname_change_notification(self, model, old, new):
        self.view['Vellum'].set_title('Vellum - %s' % (new,))

    def property_mapicon_added_change_notification(self, model, old, new):
        """Hook a new icon up to an observer"""
        if getattr(new, 'controller', None) is not self:
            new.registerObserver(self)

    def property_mapicon_removed_change_notification(self, model, old, new):
        log.msg('map icon %s removed' % (new.iconname,))

    def property_iconuri_change_notification(self, icon, old, new):
        # clean out the old widget if necessary
        if icon.widget is not None:
            icon.widget.destroy()
            icon.widget = None

        # make an image
        loc = cache.lookup(new)
        icon.image = gdk.pixbuf_new_from_file(loc)

        # scale it to correspond to the map scale
        w = icon.image.get_width()
        h = icon.image.get_height()
        scale_ratio = icon.iconsize*(100/w) / self.map.scale100px
        w = w*scale_ratio
        h = h*scale_ratio
        icon.image = icon.image.scale_simple(w,h,gdk.INTERP_HYPER)

        # place it on the canvas
        canvas = self.view['canvas']
        root = canvas.root()
        image = icon.image
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
            # outlined text
            text = icon.text = fontgroup.add("GnomeCanvasText",
                                 font="verdana bold",
                                 text=icon.iconname,
                                 )
            tw = text.get_property('text-width')
            th = text.get_property('text-height')
            textbg = fontgroup.add("GnomeCanvasRect",
                          fill_color = "white",
                          x1=-3*tw/4, y1=-3*th/4,
                          x2=3*tw/4, y2=3*th/4,
                          )
            textbg.lower_to_bottom()

            fontgroup.lower_to_bottom()


            igroup.connect('event', self.on_icon_event, icon)
            icon.widget = igroup

    def property_iconsize_change_notification(self, icon, old, new):
        # just redraw the whole icon
        icon.iconuri = icon.iconuri

    def property_iconname_change_notification(self, icon, old, new):
        # just redraw the whole icon
        icon.iconuri = icon.iconuri

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
        icon.text.set_property('fill-color', 'red')

    def on_icon_gdk_leave_notify(self, widget, event, icon):
        icon.text.set_property('fill-color', 'black')

    def on_icon_gdk_button_press(self, widget, event, icon):
        icon.grabbed = True

    def on_icon_gdk_button_release(self, widget, event, icon):
        icon.selected = not icon.selected
        icon.grabbed = False

    def on_icon_gdk_motion_notify(self, widget, event, icon):
        if icon.grabbed:
            iw, ih = icon.image.get_width(), icon.image.get_height()
            self.map.moveIcon(icon, event.x - iw/2, event.y - ih/2)

    def property_scale100px_change_notification(self, model, old, new):
        print 'map scale changed'


    def property_laser_change_notification(self, model, old, new):
        if new is None:
            self.view['laser'] = None
        else:
            if self.view['laser'] is not None:
                self.view['laser'].destroy()
            root = self.view['canvas'].root()
            x, y = new
            self.view['laser'] = root.add("GnomeCanvasEllipse", 
                    color="red", x1=x-3, y1=y-3,
                    x2=y+3, y2=y+3)

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

    def on_preferences_activate(self, widget):
        self.view['Preferences'].show()

    def on_quit_activate(self, widget):
        self.quit()

    def on_Vellum_destroy(self, widget):
        self.quit()

    def quit(self):
        log.msg("Goodbye.")
        self.deferred.callback(None)

    def on_connect_button_clicked(self, widget):
        peer = self.view['server'].get_child().get_text()
        model = self.netmodel

        # do recent_server list housekeeping - max 10 entries, put most
        # recent first, etc.
        recent = model.recent_servers
        if peer in recent:
            recent.remove(peer)
        recent.insert(0, peer)
        if len(recent) > 10:
            del recent[10:]
        set_model_from_list(self.view['server'], model.recent_servers)
        model.saveIni()

        # making this assignment connects us!
        model.server = peer

    def on_canvas_button_press_event(self, widget, ev):
        pass
    def on_canvas_button_release_event(self, widget, ev):
        pass
    def on_canvas_motion_notify_event(self, widget, ev):
        pass


# borrowed from PyGTK FAQ
def set_model_from_list (cb, items):
    """Setup a ComboBox or ComboBoxEntry based on a list of strings."""           
    model = gtk.ListStore(str)
    for i in items:
        model.append([i])
    cb.set_model(model)
    if type(cb) == gtk.ComboBoxEntry:
        cb.set_text_column(0)
    elif type(cb) == gtk.ComboBox:
        cell = gtk.CellRendererText()
        cb.pack_start(cell, True)
        cb.add_attribute(cell, 'text', 0)

