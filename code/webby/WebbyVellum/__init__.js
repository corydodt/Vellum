// import Nevow.Athena
// import StainedGlass
// import DeanEdwards
// import Divmod

// FIXME -- if i do not import SVGMap here, I get 
// nevow.athena.JSException: Error: nodeByDOM passed node with no containing Athena Ref ID
// ... on EVERY remote call.  I can't think of a reason why it would matter
// whether this gets imported at render time, or later, and I'm too annoyed to
// debug it.  

// import SVGMap


WebbyVellum.TopicBar = Nevow.Athena.Widget.subclass('WebbyVellum.TopicBar');
WebbyVellum.TopicBar.methods( // {{{
    function setTopic(self, topic) { // {{{
        self.node.value = topic;
    } // }}}
); // }}}

WebbyVellum.NameSelect = Nevow.Athena.Widget.subclass('WebbyVellum.NameSelect');
WebbyVellum.NameSelect.methods( // {{{
    function addName(self, name, flags) { // {{{
        var newName = document.createElement('option');
        newName.innerHTML = name;
        self.node.appendChild(newName);
    }, // }}}

    function removeName(self, name) { // {{{
        var options = self.node.getElementsByTagName('option');
        for (n=0; n<options.length; n++)
        {
            if (options[n].innerHTML == name)
            {
                self.node.removeChild(options[n]);
                break;
            }
        }
    }, // }}}

    function setNames(self, names) { // {{{
        self.node.innerHTML = '';
        for (n=0; n<names.length; n++)
        {
            self.addName(names[n], null);
        }
    } // }}}
); // }}}

WebbyVellum.AccountManager = Nevow.Athena.Widget.subclass('WebbyVellum.AccountManager');
WebbyVellum.AccountManager.methods( // {{{
    function __init__(self, node, nick) { // {{{
        WebbyVellum.AccountManager.upcall(self, '__init__', node);
        // Do this stuff instead of using athena:handler because this 
        // is the only way we get access to the event, and having access
        // to the event is the only way to preventDefault on the event
        // while retaining the ability to return the deferred.
        // Mother of God but javascript can be awful.
        DeanEdwards.addEvent(node, 'submit', 
            function onLogOnSubmit(event) { return self.onLogOnSubmit(event) });

        if (nick !== undefined) self.node.nick.value = nick;
    }, // }}}

    function onLogOnSubmit(self, event) { // {{{
        event.stopPropagation();
        event.preventDefault();

        // var node = event.target; // WRONG!
        // in FF, event.target is not the form if submit event was caused
        // by a keyboard "enter" press.  Use self.node for consistency.
        var node = self.node;

        var nick = node.nick.value;
        var channels = node.channels.value;
        // FIXME - handle blank
        var d = self.callRemote("onLogOnSubmit", nick, channels);
        return d;
    } // }}}
); // }}}


WebbyVellum.ChatEntry = Nevow.Athena.Widget.subclass('WebbyVellum.ChatEntry');
WebbyVellum.ChatEntry.methods( // {{{
    function __init__(self, node) { // {{{
        WebbyVellum.ChatEntry.upcall(self, '__init__', node);
        // Do this stuff instead of using athena:handler because this 
        // is the only way we get access to the event, and having access
        // to the event is the only way to preventDefault on the event
        // while retaining the ability to return the deferred.
        // Mother of God but javascript can be awful.
        DeanEdwards.addEvent(node, 'submit', 
            function chatMessage(event) { return self.submit(event) });
    }, // }}}

    function submit(self, event) { // {{{
        event.stopPropagation();
        event.preventDefault();
        var active = self.widgetParent.activeTabId();
        var input = self.firstNodeByAttribute('class', 'chatentry');
        var d = self.callRemote("chatMessage", input.value, active);
        input.value = "";
        return d;
    } // }}}
); // }}}

WebbyVellum.IRCContainer = StainedGlass.Enclosure.subclass('WebbyVellum.IRCContainer');
WebbyVellum.IRCContainer.methods( // {{{
    function activeTabId(self) { // {{{
        return self.childWidgets[1].activeTabId();
    } // }}}
); // }}}

WebbyVellum.Signup = Nevow.Athena.Widget.subclass('WebbyVellum.Signup');
WebbyVellum.Signup.methods( // {{{
    function __init__(self, node) { // {{{
        WebbyVellum.Signup.upcall(self, '__init__', node);
        DeanEdwards.addEvent(node, 'submit', 
            function processSignup(event) { return self.submit(event) });
    }, // }}}

    function submit(self, event) { // {{{
        event.stopPropagation();
        event.preventDefault();
        var message = self.firstNodeByAttribute('class', 'message');

        var email = self.node.email.value;
        if (email == '')
        {
            message.innerHTML = 'Please fill in your email address.';
            return null;
        }

        var password1 = self.node.password1.value;
        var password2 = self.node.password2.value;
        if (password1 == '' || password2 == '')
        {
            message.innerHTML = 'Please fill in your new password twice.';
            return null;
        }
        if (password1 != password2)
        {
            message.innerHTML = "Passwords don't match! Try again.";
            return null;
        }

        var submit = self.node.signup;
        submit.style['display'] = 'none';
        message.innerHTML = 'Sending email. (This may take a minute.) . . . .';

        var d = self.callRemote("processSignup", email, password1);
        d.addCallback(function _(status) {
            message.innerHTML = 'An email has been sent to the above address.';
        });
        d.addErrback(function _(failure) {
            message.innerHTML = 'An error occurred signing you up.  Maybe that account is already signed up.';
            submit.style['display'] = '';
        });
        return d;
    } // }}}
); // }}}

WebbyVellum.FileChooser = Nevow.Athena.Widget.subclass('WebbyVellum.FileChooser');
WebbyVellum.FileChooser.methods( // {{{
    function __init__(self, node) { // {{{
        WebbyVellum.FileChooser.upcall(self, '__init__', node);
        var newDocumentNode = self.firstNodeByAttribute('name', 'documentNew');
        DeanEdwards.addEvent(newDocumentNode, 'click', 
            function handleNewDocument(event) { 
                return self.handleNewDocument(event) 
        });
    }, // }}}

    function handleNewDocument(self, event) { // {{{
        event.stopPropagation();
        event.preventDefault();
        self._newUploadFrame(event.pageX, event.pageY);

        Divmod.debug("", "Clicked on FileChooser's documentNew icon");
    }, // }}}

    function _newUploadFrame(self, x, y) { // {{{
        var iframe = document.createElement('iframe');
        iframe.className = 'uploadBox';
        iframe.style['top'] = y + 'px';
        iframe.style['left'] = x + 'px';
        var body = document.getElementsByTagName('body')[0];
        iframe.src = '/upload/';
        body.appendChild(iframe);
        // when the iframe processing is done, refresh.
        window.closeUploadFrame = function _(cancelled) {
            body.removeChild(iframe);
            if (!cancelled) {
                d = self.callRemote("refresh");
                d.addCallback(function _(data) {
                    var span = self.firstNodeByAttribute('class', 'chooserArea');
                    // FIXME! instead, we should be rendering the widgets
                    span.innerHTML = data;
                });
            }
        };
    } // }}}
); // }}}

WebbyVellum.ChooserIcon = Nevow.Athena.Widget.subclass('WebbyVellum.ChooserIcon');
WebbyVellum.ChooserIcon.methods( // {{{
    function __init__(self, node) { // {{{
        WebbyVellum.ChooserIcon.upcall(self, '__init__', node);
        // draggable with droppable=true
        StainedGlass.draggable(node, null, true);
    } // }}}
); // }}}

// vi:foldmethod=marker
