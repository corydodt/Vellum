from zope.interface import Interface

class IChatEntry(Interface):
    def chatMessage(self, message, id):
        """Handler to process typed chat events on the client"""

class IChatConversations(Interface):
    def showConversation(self, conversation, conversationName):
        """Cause a conversation window to appear"""

    def hideConversation(self, conversation, conversationName):
        """Cause a conversation window to be hidden"""

    def getConversation(self, id, default):
        """Return a MinConversation object having the specified id"""

class ITextArea(Interface):
    def printClean(self, message):
        """Send text to the widget."""

class ITopicBar(Interface):
    def setTopic(self, topic):
        """Replace the topic."""

class INameSelect(Interface):
    def addName(self, name, flags=()):
        """Add a name to the list with the specified flags"""

    def removeName(self, name):
        """Remove a name from the list"""

    def setNames(self, name):
        """Set the name list, all at once (e.g. /NAMES reply)"""

class IChatAccountManager(Interface):
    def onLogOnSubmit(self, username, password, channels):
        """Handler to process an attempt to log on from the UI"""


class IMapWidget(Interface):
    def setMapBackground(self, md5key):
        """Send an image file to the remote side."""
