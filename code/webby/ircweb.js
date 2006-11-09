// import Nevow.Athena
// import Windowing
// import DeanEdwards

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

WebbyVellum.IRCContainer = Windowing.Enclosure.subclass('WebbyVellum.IRCContainer');
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

// vi:foldmethod=marker