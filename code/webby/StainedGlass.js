// import Divmod

RT = Divmod.Runtime.theRuntime;

/* abstract class that implements the state associated with a drag operation.
 * Call StainedGlass.draggable(
 */
StainedGlass.DragState = Divmod.Class.subclass('StainedGlass.DragState');
StainedGlass.DragState.methods( // {{{
    function _cleanupDragState(self) { // {{{
        DeanEdwards.removeEvent(window, 'mouseup', self.mouseup);
        DeanEdwards.removeEvent(window, 'mouseout', self.mouseout);
        DeanEdwards.removeEvent(window, 'mousemove', self.mousemove);
        self.mouseup = null;
        self.mouseout = null;
        self.mousemove = null;
        self.dragStartOffsetLeft = null;
        self.dragStartOffsetTop = null;
    }, // }}}

    function _restoreOriginalState(self) { /// {{{
        var n = self.node;
        n.style['top'] = self._savedTop;
        n.style['left'] = self._savedLeft;
        n.style['position'] = self._savedPosition;
        n.style['float'] = self._savedFloat;
    }, // }}}

    function _saveOriginalState(self) { // {{{
        var n = self.node;
        self._savedTop = n.style['top'];
        self._savedLeft = n.style['left'];
        self._savedPosition = n.style['position'];
        self._savedFloat = n.style['float'];
    }, // }}}

    function startDragging(self, event) { // {{{
        Divmod.debug("StainedGlass.DragState", "started dragging");

        // tables and things do weird stuff when you click and drag on them.
        // Don't let them do weird stuff.
        event.preventDefault();

        self._saveOriginalState();

        /* figure out the offset of the mouseclick from the top left of the
         * widget
         */
        var n = self.node;
        self.dragStartOffsetLeft = event.clientX - n.offsetLeft;
        self.dragStartOffsetTop = event.clientY - n.offsetTop;

        /* set up mousemove event to follow the movement of the mouse */
        self.mousemove = function _(event) { return self.whileDragging(event) };
        DeanEdwards.addEvent(window, 'mousemove', self.mousemove);

        /* the mouseup event could happen *anywhere* so set up 
           cancelling events on the window
        */
        self.mouseup = function _(event) { return self.stopDragging(event) };
        self.mouseout = function _(event) { return self.cancelDragging(event) };
        DeanEdwards.addEvent(window, 'mouseup', self.mouseup);
        DeanEdwards.addEvent(window, 'mouseout', self.mouseout);
    }, // }}}

    function whileDragging(self, event) { // {{{
        var n = self.node;
        n.style['position'] = 'absolute';
        n.style['float'] = 'none';
        n.style['left'] = (event.clientX - self.dragStartOffsetLeft) + 'px';
        n.style['top'] = (event.clientY - self.dragStartOffsetTop) + 'px';
    }, // }}}

    function stopDragging(self, event) { // {{{
        Divmod.debug("StainedGlass.DragState", "stopped dragging");
        self._cleanupDragState();
    }, // }}}

    function cancelDragging(self, event) { // {{{
        /* a little explanation:
         * When your mouse moves off the edge of the window, you're moving
         * FROM documentElement.
         * When you move from "dead space" into another element, you're 
         * also moving FROM documentElement, but you're moving INTO something 
         * else.
         * Therefore, the way we detect that we REALLY left the window
         * is if both target and explicitOriginalTarget are documentElement.
         */
        if (event.target === document.documentElement &&
            event.explicitOriginalTarget === document.documentElement) {
            Divmod.debug("StainedGlass.DragState", "cancelled dragging");
            self._cleanupDragState()
            self._restoreOriginalState()
            /* restore the position to the original position */
        } else {
            event.stopPropagation();
        }
    }, // }}}

    /* specify the node that will be draggable */
    function setDragHandle(self, node) { // {{{
        DeanEdwards.addEvent(node, 'mousedown', 
                function _(event) { return self.startDragging(event); }
        );
    } // }}}
); // }}}

/* Create the necessary events for a node to be draggable 
 * @arg vehicle: the node that will be moved around when you drag it
 * @arg handle: if specified, the node that you click on to move the vehicle
 */
StainedGlass.draggable = function _(vehicle, handle) { // {{{
    var dragBehavior = new StainedGlass.DragState();

    dragBehavior.node = vehicle;

    vehicle.dragBehavior = dragBehavior; // keep dragBehavior from being gc'd

    if (handle !== undefined) {
        // dragging the handle drags the node
        dragBehavior.setDragHandle(handle);
    } else {
        // dragging anywhere in the node drags the node
        dragBehavior.setDragHandle(vehicle);
    }
    return vehicle;
}; // }}}

StainedGlass.Enclosure = Nevow.Athena.Widget.subclass('StainedGlass.Enclosure');
StainedGlass.Enclosure.methods( // {{{
    function __init__(self, node) { // {{{
        StainedGlass.Enclosure.upcall(self, '__init__', node);
        try {
            var minimizer = self.firstNodeByAttribute('class', 'minimizer', null);
            DeanEdwards.addEvent(minimizer, 'click', 
                function onMinimize(event) { return self.minimize() });
            // Create an iconified node at the end of the widget's parent.
            // The iconfied version is what is shown when the widget minimizes.
            self.iconified = document.createElement('div');
            self.iconified.className = 'iconified-hidden';
            var titleParent = self.firstNodeByAttribute('class', 'windowTitle');
            var title = titleParent.innerHTML;
            self.iconified.innerHTML = '<div class="titlebar">' +
                                         '<div class="windowTitle">' +
                                            title + 
                                         '</div>' + 
                                         '<a class="minimizer">^</a>' + 
                                       '</div>';

            var restore = RT.firstNodeByAttribute(self.iconified, 'class', 
                    'minimizer');
            DeanEdwards.addEvent(restore, 'click', 
                    function onRestore(event) { return self.restore() 
            });

            node.parentNode.appendChild(self.iconified);
        } catch (e if e.toString().match(/Failed to discover .*minimizer.*/)) {
            // nothing
        }

        /* set up dragging */
        if (node.className.match(/.*\bdraggable\b.*/)) {
            var titlebar = self.firstNodeByAttribute('class', 'titlebar');
            StainedGlass.draggable(self.node, titlebar);
        }

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

StainedGlass.TextArea = Nevow.Athena.Widget.subclass('StainedGlass.TextArea');
StainedGlass.TextArea.methods( // {{{
    function __init__(self,  // {{{
                      node, 
                      /* OPTIONAL */ initialContent) {
        StainedGlass.TextArea.upcall(self, '__init__', node);

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
