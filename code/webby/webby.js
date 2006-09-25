
// import Nevow.Athena
// import Divmod

RT = Divmod.Runtime.theRuntime;

WebbyVellum.AccountManager = Nevow.Athena.Widget.subclass('WebbyVellum.AccountManager');
WebbyVellum.AccountManager.methods(
    function __init__(self, node) {
        WebbyVellum.AccountManager.upcall(self, '__init__', node);
        // Do this stuff instead of using athena:handler because this 
        // is the only way we get access to the event, and having access
        // to the event is the only way to preventDefault on the event
        // while retaining the ability to return the deferred.
        // Mother of God but javascript can be awful.
        DeanEdwards.addEvent(node, 'submit', 
            function onLogOnSubmit(event) {
                var node = event.target;
                var username = node.username.value;
                var password = node.password.value;
                var channels = node.channels.value;
                var d = self.callRemote("onLogOnSubmit", 
                        username, password, channels);
                event.stopPropagation();
                event.preventDefault();
                return d;
            });
    }
);


WebbyVellum.ChatEntry = Nevow.Athena.Widget.subclass('WebbyVellum.ChatEntry');
WebbyVellum.ChatEntry.methods(
    function __init__(self, node) {
        WebbyVellum.ChatEntry.upcall(self, '__init__', node);
        // Do this stuff instead of using athena:handler because this 
        // is the only way we get access to the event, and having access
        // to the event is the only way to preventDefault on the event
        // while retaining the ability to return the deferred.
        // Mother of God but javascript can be awful.
        DeanEdwards.addEvent(node, 'submit', 
            function chatMessage(event) {
                var active = self.widgetParent.activeTabId();
                var input = RT.firstNodeByAttribute(node, 'class', 'chatentry');
                var d = self.callRemote("chatMessage", input.value, active);
                input.value = "";
                event.stopPropagation();
                event.preventDefault();
                return d;
            });
    }
);

WebbyVellum.IRCContainer = Nevow.Athena.Widget.subclass('WebbyVellum.IRCContainer');
WebbyVellum.IRCContainer.methods(
    function activeTabId(self) {
        return self.childWidgets[1].activeTabId();
    }
);
