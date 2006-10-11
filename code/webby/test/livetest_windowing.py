from nevow import athena
from nevow.livetrial import testcase

from webby import windowing

class TestEnclosure(testcase.TestCase):
    jsClass = u'Windowing.Tests.TestEnclosure'
    def newEnclosure(self, windowTitle='~', userClass=''):
        """
        Return a new Enclosure
        """
        enc = windowing.Enclosure(windowTitle, userClass)
        enc.setFragmentParent(self)
        return enc
    athena.expose(newEnclosure)

class TestTextArea(testcase.TestCase):
    jsClass = u'Windowing.Tests.TestTextArea'
    def newTextArea(self, ):
        """
        Return a new TextArea to the browser
        """
        ta = windowing.TextArea()
        ta.setFragmentParent(self)
        return ta
    athena.expose(newTextArea)

