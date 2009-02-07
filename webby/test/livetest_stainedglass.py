from nevow import athena
from nevow.livetrial import testcase

from webby import stainedglass

class TestEnclosure(testcase.TestCase):
    jsClass = u'StainedGlass.Tests.TestEnclosure'
    def newEnclosure(self, windowTitle='~', userClass=''):
        """
        Return a new Enclosure
        """
        enc = stainedglass.Enclosure(windowTitle, userClass)
        enc.setFragmentParent(self)
        return enc
    athena.expose(newEnclosure)

class TestTextArea(testcase.TestCase):
    jsClass = u'StainedGlass.Tests.TestTextArea'
    def newTextArea(self, *a):
        """
        Return a new TextArea to the browser
        """
        ta = stainedglass.TextArea()
        ta.setFragmentParent(self)
        ta.setInitialArguments(*a)
        return ta
    athena.expose(newTextArea)

