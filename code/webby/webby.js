

// import Nevow.Athena
// import Divmod

WebbyVellum.AccountManager = Nevow.Athena.Widget.subclass('WebbyVellum.AccountManager');
WebbyVellum.AccountManager.methods(
    function onLogOnSubmit(self, node, event) {
        Divmod.debug("AccountManager", "logon clicked");
        username = node.username.value;
        password = node.password.value;
        channels = node.channels.value;
        self.callRemote("onLogOnSubmit", username, password, channels);
        return false;
    }
);


WebbyVellum.ChatEntry = Nevow.Athena.Widget.subclass('WebbyVellum.ChatEntry');
WebbyVellum.ChatEntry.methods(
    function chatMessage(self, node, event) {
        Divmod.debug("ChatEntry", event);
        var input = Nevow.Athena.FirstNodeByAttribute(node,
            'class', 'chatentry')
        self.callRemote("chatMessage", input.value);
        input.value = "";
        return false;
    }
);
