// import Nevow.Athena
// import DeanEdwards
// import Divmod

SVGNS = 'http://www.w3.org/2000/svg';
XLINKNS = 'http://www.w3.org/1999/xlink';

SVGMap.MapWidget = Nevow.Athena.Widget.subclass('SVGMap.MapWidget');
SVGMap.MapWidget.methods( // {{{
    function __init__(self, node) // {{{
    {
        SVGMap.MapWidget.upcall(self, '__init__', node);
        DeanEdwards.addEvent(node, 'mouseup', function onmouseup(event) { 
            return self.checkForDrop(event); 
        });
    }, // }}}

    /* true if there is a background image set for this widget */
    function hasBackground(self) { // {{{
        if (self.childWidgets === undefined) return false;
        try {
            if (self.childWidgets[0].nodeById('map-background')) return true;
            return false;
        } catch (e) {
            return false;
        }
    }, // }}}

    /* if a node is being dropped here, do something about it */
    function checkForDrop(self, event) { // {{{
        if (window.droppable) {
            var chooserIcon = window.droppable;
            var cl = chooserIcon.className;

            /* ignore any droppables that don't have class chooserIcon */
            if (! cl.match(/.*\bchooserIcon\b.*/)) return;

            /* only set a new background if background is blank */
            if (self.hasBackground()) return;

            /* only set if the chooserIcon that was dropped is an image */
            var img = chooserIcon.getElementsByTagName('img')[0];
            if (img === undefined || ! img.src.match(/.*\/thumb$/)) return;

            return self.sendBackgroundCommand(img);
        }
    }, // }}}

    /* send a /BACKGROUND command */
    function sendBackgroundCommand(self, img) { // {{{
        var tabid = self.getContainer().activeTabId();
        var md5key = self._parseSrcForMd5key(img.src);
        var command = "/BACKGROUND " + tabid + " " + md5key;
        var d = self.callRemote("sendCommand", command);
        d.addErrback(function _(failure) {
            Divmod.debug("", failure);
            debugger;
            return failure;
        });
        return d;
    }, // }}}

    /* search upwards until we find the irc container
     */
    function getContainer(self) { // {{{
        var nn = self.node;
        while (nn.parentNode) {
            nn = nn.parentNode;
            if (nn.className.match(/\birc\b/)) break;
        }
        return Nevow.Athena.Widget.get(nn);
    }, // }}}

    /* place a new BackgroundImage widget in the empty channel map */
    function setMapBackground(self, backgroundInfo) { // {{{
        var d = self.addChildWidgetFromWidgetInfo(backgroundInfo);
        d.addCallback(function gotBackgroundWidget(background) {
            var images = background.node.getElementsByTagName('image');
            var bgimage = images[0];
            var obimage = images[1];

            var w = bgimage.getAttribute('width');
            var h = bgimage.getAttribute('height');

            var nn = self.node;
            nn.setAttribute('width', w);
            nn.setAttribute('height', h);
            nn.appendChild(background.node);

            // FIXME - don't know why I have to set the href again.
            bgimage.setAttributeNS(XLINKNS, 'href', bgimage.href.baseVal);
            obimage.setAttributeNS(XLINKNS, 'href', obimage.href.baseVal);
            return null;
        });
        return d;
    }, // }}}

    /* replace the href for the obscurement widget in the existing channel map
     */
     function updateObscurement(self, md5key) { // {{{
        var images = self.childWidgets[0].node.getElementsByTagName('image');
        var obimage = images[1];
        obimage.setAttributeNS(XLINKNS, 'href', '/files/' + md5key);
     }, // }}}

    /* takes a string of the form /files/...md5.../thumb or similar and
       returns the md5 key
       */
    function _parseSrcForMd5key(self, src) { // {{{
        return src.replace(/.*\/files\/(.*)\/thumb/, "$1");
    } // }}}
); // }}}

// vi:foldmethod=marker
