// import Nevow.Athena
// import Divmod
// import DeanEdwards


RT = Divmod.Runtime.theRuntime;

Tabby.TabsElement = Nevow.Athena.Widget.subclass("Tabby.TabsElement");
Tabby.TabsElement.methods(
    function activeTabId(self)
    {
        return self._activeTabId;
    },

    function clicked(self, node)
    {
        self._clicked(node);
    },

    function show(self, id)
    {
        var handle = self.getHandleForId(id);
        self._clicked(handle);
    },

    function _clicked(self, handle)
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
    },

    function addTab(self, id, label, /* optional */ scrollback)
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
        pane.setAttribute('id', id);
        pane.className = 'tab';
        // pane is created empty initially.


        var handles = self.firstNodeByAttribute('class', 'handles');
        handles.appendChild(handle);
        var panes = self.firstNodeByAttribute('class', 'panes');
        panes.appendChild(pane);

        self._clicked(handle);

        if (scrollback === undefined)
        {
            scrollback = 1000; // 1000 whats? :-)
        }
        // TODO - set up length of scrollback with optional scrollback arg

    },

    function removeTab(self, id)
    {
        var handle = self.getHandleForId(id);
        var handles = self.firstNodeByAttribute('class', 'handles');
        handles.removeChild(handle);

        var pane = self.getPaneForId(id);
        var panes = self.firstNodeByAttribute('class', 'panes');
        panes.removeChild(pane);

    },

    function appendToTab(self, id, content)
    {
        var pane = self.getPaneForId(id);
        // TODO - deal with scrollback length of node
        RT.appendNodeContent(pane, content);
        pane.scrollTop = pane.scrollHeight;
    },

    function getPaneForId(self, id)
    {
        return self.firstNodeByAttribute('id', id);
    },

    function getHandleForId(self, id)
    {
        return self.firstNodeByAttribute('href', '#' + id);
    },

    function __init__(self, node, 
                      /* optional */ initialTabId, initialTabLabel,
                      /* optional */ nodeContent)
    {
        Tabby.TabsElement.upcall(self, '__init__', node);
        if (initialTabId !== undefined)
        {
            if (initialTabLabel !== undefined)
            {
                self.addTab(initialTabId, initialTabLabel);
                if (nodeContent !== undefined)
                {
                    self.appendToTab(initialTabId, nodeContent);
                }
            } else {
                Divmod.debug("TabsElement", 
                    "initialTabId provided to __init__ without initialTabLabel");
            }
        }
    }
);
