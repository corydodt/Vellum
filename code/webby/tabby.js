// import Nevow.Athena
// import Divmod

// add events in a cross-browser way
function xbAddEvent(obj, evType, fn, useCapture){
  if (obj.addEventListener){
    obj.addEventListener(evType, fn, useCapture);
    return true;
  } else if (obj.attachEvent){
    var r = obj.attachEvent("on"+evType, fn);
    return r;
  } else {
    alert("Handler could not be attached");
  }
}

Tabby.TabsFragment = Nevow.Athena.Widget.subclass("Tabby.TabsFragment");
Tabby.TabsFragment.methods(
    function clicked(self, node, event)
    {
        self._clicked(node);
    },

    function _clicked(self, handle)
    {
        Divmod.debug("TabsFragment", "clicked..." + handle.getAttribute("href"));
        var href = handle.getAttribute('href').replace("#", "");
        var others = Divmod.Runtime.theRuntime.nodesByAttribute(self.node, 'class', 'tab');
        for (var i=0;i<others.length;i++)
        {
            // FTR: node.setAttribute('class', ..) is broken in IE, thus
            // we use this.  className is all over the place in this file.
            others[i].className = 'bg-tab';
        }
        var mate = Nevow.Athena.FirstNodeByAttribute(self.node, 'id', href);
        mate.className = 'tab';

        return false;
    },

    function addTab(self, id, label)
    {
        var handle = document.createElement('a');
        handle.setAttribute('href', '#' + id);
        handle.className = 'tab-handle';
        handle.appendChild(document.createTextNode(label));

        function _clickWrap(ev)
        {
            return self.clicked(handle, ev);
        }

        xbAddEvent(handle, 'click', _clickWrap, true);

        var pane = document.createElement('div');
        pane.setAttribute('id', id);
        pane.className = 'tab';
        var junk = document.createElement('h3');
        junk.appendChild(document.createTextNode(label + ' Contents'));
        pane.appendChild(junk);


        var handles = Nevow.Athena.FirstNodeByAttribute(self.node,
            'class',
            'handles');
        handles.appendChild(handle);
        var panes = Nevow.Athena.FirstNodeByAttribute(self.node,
            'class',
            'panes');
        panes.appendChild(pane);
        self.buffers[id] = pane;

        self._clicked(handle);

    },

    function removeTab(self, id)
    {
        handle = Nevow.Athena.FirstNodeByAttribute(self.node, 'href', '#'+id);
        var handles = Nevow.Athena.FirstNodeByAttribute(self.node,
            'class',
            'handles');
        handles.removeChild(handle);

        pane = Nevow.Athena.FirstNodeByAttribute(self.node, 'id', id);
        var panes = Nevow.Athena.FirstNodeByAttribute(self.node,
            'class',
            'panes');
        panes.removeChild(pane);

        self.buffers[id] = null;
    },

    function __init__(self, node)
    {
        Tabby.TabsFragment.upcall(self, '__init__', node);
        self.buffers = new Object;
        self.addTab('one', 'Tab One');
        self.addTab('foo', 'Tab Foo');
        self.addTab('three', 'Tab Three');
        self.removeTab('foo');
    }
);
