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

>>> Enclosure(windowTitle="My StainedGlass", userClass="someWindowOfMine")

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

from zope.interface import implements

from webby import util, iwebby, RESOURCE

class Enclosure(athena.LiveElement):
    """
    @ivar windowTitle: A title that will be shown at the top of the widget
    @ivar userClass: additional text to add at the end of the class=".." attribute
    @ivar decorated: if False, no decorations (border, titlebar, etc.)
    """
    jsClass = u"StainedGlass.Enclosure"
    docFactory = loaders.xmlfile(RESOURCE('elements/Enclosure'))
    def __init__(self, windowTitle='~', userClass='', decorated=True, *a, **kw):
        super(Enclosure, self).__init__(*a, **kw)
        self.windowTitleStan = windowTitle
        self.userClassStan = userClass
        self.children = []
        self.decorated = decorated

    def enclosedRegion(self, request, tag):
        return tag[self.children]

    athena.renderer(enclosedRegion)

    def __getitem__(self, children):
        self.children = children
        return self

    def extraClasses(self, request, tag):
        tag.fillSlots('userClass', self.userClassStan)
        if self.decorated:
            tag.fillSlots('decorationClass', 'decorated')
        else:
            tag.fillSlots('decorationClass', '')
        return tag

    athena.renderer(extraClasses)

    def windowTitle(self, request, tag):
        tag.fillSlots('windowTitle', self.windowTitleStan)
        return tag

    athena.renderer(windowTitle)

    def decorations(self, req, tag):
        if self.decorated:
            return tag
        return []

    athena.renderer(decorations)

class TextArea(util.RenderWaitLiveElement):
    """A scrollable widget that displays mostly lines of text."""
    implements(iwebby.ITextArea) # FIXME - move to here
    jsClass = u"StainedGlass.TextArea"
    docFactory = loaders.xmlfile(RESOURCE('elements/TextArea'))
    widgetArgs = None

    def __init__(self, *a, **kw):
        super(TextArea, self).__init__(*a, **kw)
        self.messageQueue = []

    def printClean(self, message):
        """
        Send text to the widget if it is ready; if not, queue text
        for later.
        """
        message = util.flattenMessageString(message)
        return self.callRemote('appendTo', message)

    def setInitialArguments(self, *a, **kw): # FIXME - raped from tabs.py
        assert len(kw) == 0, "Cannot pass keyword arguments to a Widget"
        self.widgetArgs = a

    def getInitialArguments(self): # FIXME - raped from tabs.py
        args = ()
        if self.widgetArgs is not None:
            args = self.widgetArgs

        return args

