// import Divmod

RT = Divmod.Runtime.theRuntime;

Windowing.Enclosure = Nevow.Athena.Widget.subclass('Windowing.Enclosure');
Windowing.Enclosure.methods( // {{{
    function __init__(self, node) { // {{{
        Windowing.Enclosure.upcall(self, '__init__', node);
        var minimizer = self.firstNodeByAttribute('class', 'minimizer');
        DeanEdwards.addEvent(minimizer, 'click', 
            function onMinimize(event) { return self.minimize() });

        // Create an iconified node at the end of the widget's parent.
        // The iconfied version is what is shown when the widget minimizes.
        self.iconified = document.createElement('div');
        self.iconified.className = 'iconified-hidden';
        var titleParent = self.firstNodeByAttribute('class', 'windowTitle');
        var title = titleParent.innerHTML;
        self.iconified.innerHTML = '<div class="titlebar">' +
                                     '<div class="windowTitle">' +title+ '</div>' + 
                                     '<a class="minimizer">^</a>' + 
                                   '</div>';

        var restore = RT.firstNodeByAttribute(self.iconified, 'class', 'minimizer');
        DeanEdwards.addEvent(restore, 'click', 
            function onRestore(event) { return self.restore() });

        node.parentNode.appendChild(self.iconified);
    }, // }}}

    function minimize(self) { // {{{
        var n = self.node;
        n.className = n.className.replace('enclosure', 'enclosure-hidden');
        var icon = self.iconified;
        icon.className = icon.className.replace('iconified-hidden', 'iconified');
    }, // }}}

    function restore(self) { // {{{
        var n = self.node;
        n.className = n.className.replace('enclosure-hidden', 'enclosure');
        var icon = self.iconified;
        icon.className = icon.className.replace('iconified', 'iconified-hidden');
    } // }}}
); // }}}

Windowing.TextArea = Nevow.Athena.Widget.subclass('Windowing.TextArea');
Windowing.TextArea.methods( // {{{
    function __init__(self,  // {{{
                      node, 
                      /* OPTIONAL */ initialContent) {
        Windowing.TextArea.upcall(self, '__init__', node);

        if (initialContent !== undefined)
            self.appendTo(initialContent);
    }, // }}}

    function appendTo(self, content) // {{{
    {
        RT.appendNodeContent(self.node, content);
        self.node.scrollTop = self.node.scrollHeight;
    } // }}}
); // }}}

// vi:foldmethod=marker
