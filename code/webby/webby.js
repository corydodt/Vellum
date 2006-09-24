
// import Nevow.Athena
// import Divmod

RT = Divmod.Runtime.theRuntime;

WebbyVellum.AccountManager = Nevow.Athena.Widget.subclass('WebbyVellum.AccountManager');
WebbyVellum.AccountManager.methods(
    function onLogOnSubmit(self, node, event) {
        var username = node.username.value;
        var password = node.password.value;
        var channels = node.channels.value;
        var d = self.callRemote("onLogOnSubmit", username, password, channels);
        event.cancelBubble = true;
        return d;
    }
);


WebbyVellum.ChatEntry = Nevow.Athena.Widget.subclass('WebbyVellum.ChatEntry');
WebbyVellum.ChatEntry.methods(
    function chatMessage(self, node, event) {
        var active = self.widgetParent.activeTabId();
        var input = RT.firstNodeByAttribute(node, 'class', 'chatentry');
        var d = self.callRemote("chatMessage", input.value, active);
        input.value = "";
        event.cancelBubble = true;
        return d;
    }
);

WebbyVellum.IRCContainer = Nevow.Athena.Widget.subclass('WebbyVellum.IRCContainer');
WebbyVellum.IRCContainer.methods(
    function activeTabId(self) {
        return self.childWidgets[1].activeTabId();
    }
);
