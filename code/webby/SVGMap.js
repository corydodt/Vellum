// import Nevow.Athena
// import DeanEdwards
// import Divmod

SVGMap.MapWidget = Nevow.Athena.Widget.subclass('SVGMap.MapWidget');
SVGMap.MapWidget.methods( // {{{
    function __init__(self, node) // {{{
    {
        SVGMap.MapWidget.upcall(self, '__init__', node);
        DeanEdwards.addEvent(node, 'mouseup', 
                function onmouseup(event) { return self.checkForDrop(event); 
        });
    }, // }}}

    /* if a node is being dropped here, do something about it */
    function checkForDrop(self, event) { // {{{
        Divmod.debug("SVGMap.MapWidget", "Mouse was upped here.");
    } // }}}
); // }}}

// vi:foldmethod=marker
