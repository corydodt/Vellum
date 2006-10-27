"""
Elements for constructing a window interface.


========================================
Flexible Enclosure (dumb window) Element
========================================

Use one of these for slightly window-like appearance and behavior around a
widget.

Has no callRemotes, but it supports inheritance so you can do things like
notify the iconified window when something on the server generates an event.
(These callRemotes may be added in the future.)

>>> Enclosure(windowTitle="My Window", userClass="someWindowOfMine")

The "userClass" init arg will be inserted into the 'class' attribute of the
node.


===========================
Scrolling Text Area Element
===========================

Use one of these for a console-like text area.

Supports callRemotes for:

    appendTo(content) -> a single, XHTML-namespaced node to add to the widget

"""

from twisted.python.util import sibpath

from nevow import loaders, athena

from webby import util

RESOURCE = lambda f: sibpath(__file__, f)

class Enclosure(athena.LiveElement):
    jsClass = u"Windowing.Enclosure"
    docFactory = loaders.xmlfile(RESOURCE('elements/Enclosure'))
    def __init__(self, windowTitle='~', userClass='', *a, **kw):
        super(Enclosure, self).__init__(*a, **kw)
        self.windowTitleStan = windowTitle
        self.userClassStan = userClass

    def enclosedRegion(self, request, tag):
        return tag['']
    athena.renderer(enclosedRegion)

    def userClass(self, request, tag):
        tag.fillSlots('userClass', self.userClassStan)
        return tag
    athena.renderer(userClass)

    def windowTitle(self, request, tag):
        tag.fillSlots('windowTitle', self.windowTitleStan)
        return tag
    athena.renderer(windowTitle)



class TextArea(athena.LiveElement):
    """A scrollable widget that displays mostly lines of text."""
    jsClass = u"Windowing.TextArea"
    docFactory = loaders.xmlfile(RESOURCE('elements/TextArea'))
    widgetArgs = None

    readyToSend = False

    def __init__(self, *a, **kw):
        super(TextArea, self).__init__(*a, **kw)
        self.messageQueue = []

    def ready(self):
        """Mark widget as ready to send data, and flush the pending queue"""
        assert not self.readyToSend, "TextArea.ready() called twice"
        self.readyToSend = True
        for m in self.messageQueue:
            self._reallyPrintClean(m)

    def printClean(self, message):
        """
        Send text to the widget if it is ready; if not, queue text
        for later.
        """
        message = util.flattenMessageString(message)
        if self.readyToSend:
            self._reallyPrintClean(message)
        else:
            self.messageQueue.append(message)

    def _reallyPrintClean(self, message):
        return self.callRemote('appendTo', message)

    def setInitialArguments(self, *a, **kw): # FIXME - raped from tabs.py
        assert len(kw) == 0, "Cannot pass keyword arguments to a Widget"
        self.widgetArgs = a

    def getInitialArguments(self): # FIXME - raped from tabs.py
        args = ()
        if self.widgetArgs is not None:
            args = self.widgetArgs

        return args

