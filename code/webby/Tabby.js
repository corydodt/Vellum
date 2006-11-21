// import Nevow.Athena
// import Divmod
// import Divmod.Defer
// import DeanEdwards


RT = Divmod.Runtime.theRuntime;

Tabby.TabsElement = Nevow.Athena.Widget.subclass("Tabby.TabsElement");
Tabby.TabsElement.methods( // {{{
    function activeTabId(self) // {{{
    {
        return self._activeTabId;
    }, // }}}

    function clicked(self, node) // {{{
    {
        self._clicked(node);
    }, // }}}

    function show(self, id) // {{{
    {
        var handle = self.getHandleForId(id);
        self._clicked(handle);
    }, // }}}

    function _clicked(self, handle) // {{{
    {
        Divmod.debug("TabsElement", "clicked..." + handle.getAttribute("href"));
        var id = handle.getAttribute('href').substr(1);

        // set classes on all the panes, either background (bg) or regular
        var other_panes = self.nodesByAttribute('class', 'tab');
        for (var i=0;i<other_panes.length;i++)
        {
            // FTR: node.setAttribute('class', ..) is broken in IE, thus
            // we use this.  className is all over the place in this file.
            other_panes[i].className = 'bg-tab';
        }
        var mate = self.firstNodeByAttribute('id', id);
        mate.className = 'tab';

        // set classes on all the handles, either background (bg) or regular
        var other_handles = self.nodesByAttribute('class', 'tab-handle');
        for (var i=0;i<other_handles.length;i++)
        {
            other_handles[i].className = 'bg-tab-handle';
        }
        handle.className = 'tab-handle';

        self._activeTabId = id;

        return false;
    }, // }}}

    function addTab(self, id, label) // {{{
    {
        var handle = document.createElement('a');
        handle.setAttribute('href', '#' + id);
        handle.className = 'tab-handle';
        handle.appendChild(document.createTextNode(label));

        function _clickWrap(ev)
        {
            ev.stopPropagation();
            ev.preventDefault();
            return self.clicked(handle);
        }

        DeanEdwards.addEvent(handle, 'click', _clickWrap);

        var pane = document.createElement('div');
        pane.setAttribute('id', id); // FIXME - need a really unique ID!
        pane.className = 'tab';
        // pane is created empty initially.


        var handles = self.firstNodeByAttribute('class', 'handles');
        handles.appendChild(handle);
        var panes = self.firstNodeByAttribute('class', 'panes');
        panes.appendChild(pane);

        self._clicked(handle);

    }, // }}}

    function removeTab(self, id) // {{{
    {
        var handle = self.getHandleForId(id);
        var handles = self.firstNodeByAttribute('class', 'handles');
        handles.removeChild(handle);

        var pane = self.getPaneForId(id);
        var panes = self.firstNodeByAttribute('class', 'panes');
        panes.removeChild(pane);

        self._clicked(handles.lastChild);
    }, // }}}

    /* add a content string as nodes to the end of the tab pane */
    function appendToTab(self, id, content) // {{{
    {
        var pane = self.getPaneForId(id);
        RT.appendNodeContent(pane, content);
        pane.scrollTop = pane.scrollHeight; // FIXME - remove this when we start using TextAreas
    }, // }}}

    /* make a widget a child of this widget, and add the widget node to the
       end of the tab pane
     */
    function appendWidgetInfoToTab(self, id, info) // {{{
    {
        var d = self.addChildWidgetFromWidgetInfo(info);
        d.addCallback(function _(w) {
            var pane = self.getPaneForId(id);
            pane.appendChild(w.node);
            return null;
        });
        d.addErrback(function _(failure) {
            Divmod.debug("", "Could not add widget because " + failure);
            return failure;
        });
        return d;
    }, // }}}

    function setTabBody(self, id, content) // {{{
    {
        if (content.markup !== undefined)
        {
            // this is a widget.
            return self.appendWidgetInfoToTab(id, content);
        } else {
            // just some regular content.
            return Divmod.Defer.succeed(self.appendToTab(id, content));
        };
    }, // }}}

    function getPaneForId(self, id) // {{{
    {
        return self.firstNodeByAttribute('id', id);
    }, // }}}

    function getHandleForId(self, id) // {{{
    {
        return self.firstNodeByAttribute('href', '#' + id);
    }, // }}}

    function __init__(self, node /* optional arguments */)
    {
        Tabby.TabsElement.upcall(self, '__init__', node);
        for (var i=2; i<arguments.length; i++) {
            var tab = arguments[i];
            var initialTabId = tab[0];
            var initialTabLabel = tab[1];
            var nodeContent = tab[2];
            self.addTab(initialTabId, initialTabLabel);
            var d = self.setTabBody(initialTabId, nodeContent);
        }
    } // }}}
); // }}}

// vi:foldmethod=marker
