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


// slow.  FIXME - use a schwartzian transform to sort.
WebbyVellum.icmp = function icmp(a, b) { // {{{
    var a = a.toString().toLowerCase();
    var b = b.toString().toLowerCase();
    if (a == b) return 0;
    return (a > b ? 1 : -1);
} // }}}


WebbyVellum.TopicBar = Nevow.Athena.Widget.subclass('WebbyVellum.TopicBar');
WebbyVellum.TopicBar.methods( // {{{
    function setTopic(self, topic) { // {{{
        self.node.value = topic;
    } // }}}
); // }}}

WebbyVellum.insertSorted = function insertSorted(name, flags, options, inserter) { // {{{
    // TODO - sort ops at the top, voice next, lurkers last
    var lname = name.toLowerCase();
    for (var i=0; i < options.length; i++) {
        if (options[i].innerHTML.toLowerCase() > lname) {
            inserter(name, options[i]);
            return;
        }
    }
    // now we're at the end of the list
    inserter(name, null);
}; // }}}

/* return a function that can insert an item into the select list */
function getInserter(select) // {{{
{
    return function _(name, before) {
        var newName = document.createElement('option');
        newName.innerHTML = name;
        select.add(newName, before);
    }
} // }}}

WebbyVellum.NameSelect = Nevow.Athena.Widget.subclass('WebbyVellum.NameSelect');
WebbyVellum.NameSelect.methods( // {{{
    function addName(self, name, flags) { // {{{
        WebbyVellum.insertSorted(name, flags, self.node.options, 
                getInserter(self.node));
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
        names.sort(WebbyVellum.icmp);

        var ins = getInserter(self.node);
        for (var n=0; n<names.length; n++)
        {
            ins(names[n], null);
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
        d.addCallback(function finishedLogOn(r) {
            if (r.match(/connected .*/)) {
                self.node.style['display'] = 'none';
            }
            return r;
        });
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
        var input = self.node.chatentry;
        var ret = self.sendChatText(input.value);
        input.value = "";
        return ret;
    }, // }}}

    function sendChatText(self, text) { // {{{
        return self.callRemote("chatMessage", text);
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
        message.innerHTML = 'Sending email. (This may take a minute.)' +
                '<img src="/static/loading.gif" />';

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
        var newDocumentNode = self.firstNodeByClass('documentNew');
        DeanEdwards.addEvent(newDocumentNode, 'click', 
            function handleNewDocument(event) { 
                return self.handleNewDocument(event) 
        });
        window.closeUploadFrame = null;
    }, // }}}

    /* return 2-arrays of all icons in the chooser */
    function _iconsByLabel(self) { // {{{
        var ret = [];
        for (var i=0; i<self.childWidgets.length; i++) {
            var wid = self.childWidgets[i];
            var label = wid.nodeById('chooserIconLabel').innerHTML;
            ret.push([label, wid]);
        }
        return ret;
    }, // }}}

    /* modify in-place to put icons in label-sorted order */
    function sortFilenames(self) { // {{{
        var _icons = self._iconsByLabel();
        _icons.sort(WebbyVellum.icmp);
        self.innerHTML = '';
        for (var i=0; i<_icons.length; i++) {
            self.node.appendChild(_icons[i][1].node);
        }
    }, // }}}

    function handleNewDocument(self, event) { // {{{
        event.stopPropagation();
        event.preventDefault();
        self._newUploadFrame(event.pageX, event.pageY);

        Divmod.debug("", "Clicked on FileChooser's documentNew icon");
    }, // }}}

    function fileAdded(self, iconinfo) { // {{{
        var d = self.addChildWidgetFromWidgetInfo(iconinfo);
        d.addCallback(function gotIcon(icon) {
            self.sortFilenames();
            return null;
        });
        return d;
    }, // }}}

    function _newUploadFrame(self, x, y) { // {{{
        if (window.closeUploadFrame === null) {
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
                window.closeUploadFrame = null;
            };
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

WebbyVellum.ConversationEnclosure = Nevow.Athena.Widget.subclass('WebbyVellum.ConversationEnclosure');
WebbyVellum.ConversationEnclosure.methods( // {{{
    function __init__(self, node, conversationName) { // {{{
        WebbyVellum.ConversationEnclosure.upcall(self, '__init__', node);
        self.conversationName = conversationName;
        self.chatentry = null;
        // Using nodesByAttribute instead of firstNodeByAttribute because
        // it doesn't raise an exception when no nodes are found.
        // Channel conversations have this, private convs do not.
        self.toolbar = self.nodesByClass('toolbar')[0];
        if (self.toolbar !== undefined) {
            var makeHandler = function (handler, src) {
                var button = self.firstNodeByAttribute('src', src);
                DeanEdwards.addEvent(button, 'click', handler);
            };
            /*
            makeHandler(self.onRevealClicked, "/static/tog-reveal-22.png");
            makeHandler(self.onObscureClicked, "/static/tog-obscurement-22.png");
            */
            makeHandler(function (event) { self.onRevealAllClicked(event) }, 
                    "/static/reveal-all-22.png");
            makeHandler(function (event) { self.onObscureAllClicked(event) }, 
                    "/static/obscure-all-22.png");
            /*
            makeHandler(, "/static/document-new-22.png");
            makeHandler(, "/static/draw-path-22.png");
            makeHandler(, "/static/pan-22.png");
            makeHandler(, "/static/zoom-22.png");
            makeHandler(, "/static/zoom-full-22.png");
            makeHandler(, "/static/measure-22.png" );
            */
        }
    }, // }}}

    /* get, and memoize (as self.chatentry) the chatentry widget */
    function getChatEntry(self) { // {{{
        if (self.chatentry === null) {
            self.chatentry = Nevow.Athena.Widget.get(
                    self.widgetParent.firstNodeByClass('chatentry'));
        }
        return self.chatentry;
    }, // }}}

    function onRevealAllClicked(self, event) { // {{{
        var ce = self.getChatEntry();
        return ce.sendChatText("/REVEALALL " + self.conversationName);
    }, // }}}

    function onObscureAllClicked(self, event) { // {{{
        var ce = self.getChatEntry();
        return ce.sendChatText("/OBSCUREALL " + self.conversationName);
    } // }}}
); // }}}

// vi:foldmethod=marker
