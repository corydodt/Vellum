// import Nevow.Athena.Test
// import WebbyVellum.Tests
// import SVGMap
// import Divmod.Defer

SVGMap.Tests.MockChatEntry = Divmod.Class.subclass("SVGMap.Tests.MockChatEntry");
SVGMap.Tests.MockChatEntry.methods( // {{{
    function sendChatText(self, text) { // {{{
        return Divmod.Defer.succeed('ok');
    } // }}}
); // }}}


SVGMap.Tests.TestMapWidget = Nevow.Athena.Test.TestCase.subclass("SVGMap.Tests.TestMapWidget");
SVGMap.Tests.TestMapWidget.methods( // {{{
    function test_initialize(self) { // {{{
        var d = self.setUp();
        d.addCallback(function _(map) {
            var rect = map.node.getElementsByTagName('rect')[0];
            self.assertEqual(rect.getAttribute('stroke'), 'black');
        });
        return d
    }, // }}}

    function test_hasBackground(self) { // {{{
        var d = self.setUp();
        d.addCallback(function gotMap(map) {
            self.assertEqual(map.hasBackground(), false);
            var d2 = self.callRemote("requestSetMapBackground");
            d2.addCallback(function gotMapBackgroundInfo(bginfo) {
                return map.setMapBackground(bginfo);
            });
            d2.addCallback(function gotMapBackground(bg) {
                document.body.appendChild(map.node);
                return self.assertEqual(map.hasBackground(), true);
            });
            return d2;
        });
        return d;
    }, // }}}

    function test_checkForDropNoMap(self) { // {{{
        var d = self.setUpContainerWithMap();
        d.addCallback(function gotContainer(irc) {
            try {
                var mymap = Nevow.Athena.Widget.get(
                        irc.node.getElementsByTagName('svg')[0]);

                var ev = MockEvent(mymap.node);

                /* check that non-image droppables will be ignored */
                window.droppable = document.createElement('foop');
                window.droppable.className = 'chooserIcon';
                var ret = mymap.checkForDrop(ev);
                self.assertEqual(ret, undefined);

                /* check that droppables w/ different classes will be ignored */
                window.droppable = document.createElement('table');
                var innerImg = document.createElement('img');
                innerImg.src = '/files/xyz/thumb';
                window.droppable.appendChild(innerImg);
                window.droppable.className = 'ignoreThis';
                var ret = mymap.checkForDrop(ev);
                self.assertEqual(ret, undefined);

                /* check that our droppable will work even when there are
                 * other class tags
                 */
                window.droppable.className = 'ignoreThis chooserIcon';
                var ret = mymap.checkForDrop(ev);
                ret.addErrback(function _(failure) { 
                    self.fail(failure)
                });
                ret.addCallback(function _(res) {
                    self.assertEqual(res, 'ok');
                });

            } finally {
                window.droppable = undefined;
            }
        });
        return d;
    }, // }}}
    
    /* see what happens when a mapwidget already has the background */
    function test_checkForDropPresetMap(self) { // {{{
        var d = self.setUpContainerWithMapAndBackground();
        d.addCallback(function gotContainer(irc) {
            var map = Nevow.Athena.Widget.get(
                    irc.node.getElementsByTagName('svg')[0]);

            var ret = map.checkForDrop(MockEvent(map.node));
            self.assertEqual(ret, undefined);
        });
        return d;
    }, // }}}


    /* create an irc container that contains a mapwidget */
    function setUpContainerWithMap(self) { // {{{
        var d = self.setUp();
        d.addCallback(function gotMap(map) {
            var d2 = self.callRemote("newMapWidgetInContainer");
            d2.addCallback(function gotContainerInfo(info) { 
                return self.addChildWidgetFromWidgetInfo(info);
            });
            d2.addCallback(function gotIrc(irc) { 
                // just put the map node into the container, bypassing irc
                // login
                irc.node.appendChild(map.node);
                // monkey patch the ChatEntry in the container with our mock one.
                irc.childWidgets[2] = SVGMap.Tests.MockChatEntry();
                return irc;
            });
            return d2;
        });
        return d;
    }, // }}}

    /* create an irc container that contains a mapwidget with hasBackground
     * returning true
     */
    function setUpContainerWithMapAndBackground(self) { // {{{
        var d = self.setUpContainerWithMap();
        d.addCallback(function gotContainer(irc) {
            var map = Nevow.Athena.Widget.get(
                    irc.node.getElementsByTagName('svg')[0]);
            map.hasBackground = function (self) { return true; };
            /*
            var image = document.createElementNS(SVGNS, 'image');
            image.setAttribute('id',
                    'athenaid:'
                    +mymap.childWidgets[0].objectID+
                    '-map-background');
            mymap.node.appendChild(image);
            */
            return irc;
        });
        return d;
    }, // }}}

    /* test that setMapBackground can set up the SVG widgets when it gets
       a BackgroundImage widget from the server
     */
    function test_setMapBackground(self) { // {{{
        var d = self.setUp();
        var mymap = null;
        d.addCallback(function gotMap(map) {
            mymap = map;
            return self.callRemote("requestSetMapBackground");
        });
        d.addCallback(function gotBackgroundInfo(info) { 
            return mymap.setMapBackground(info);
        });
        d.addCallback(function gotBackground(background) {
            self.assertEqual(mymap.node.getAttribute('width'), '100');
            self.assertEqual(mymap.node.getAttribute('height'), '100');

            var images = background.node.getElementsByTagName('image');
            var bgimage = images[0];
            var obimage = images[1];

            self.assertEqual(bgimage.getAttributeNS(XLINKNS, 'href'), 
                    '/files/c2d8ac97a07cbf785d2e4d7dbf578d2c');
        });
        return d;
    }, // }}}

    function test_sendBackgroundCommand(self) { // {{{
        var d = self.setUpContainerWithMap();
        d.addCallback(function gotContainer(irc) {
            var map = Nevow.Athena.Widget.get(
                    irc.node.getElementsByTagName('svg')[0]);
            var img = document.createElement('img');
            var d2 = map.sendBackgroundCommand(img);
            d2.addCallback(function sendCommand(ret) {
                self.assertEqual(ret, 'ok');
            });
        });
        return d;
    }, // }}}

    function setUp(self) { // {{{
        var d = self.callRemote("newMapWidget");
        d.addCallback(
            function _(wi) { return self.addChildWidgetFromWidgetInfo(wi); }
            );
        return d;
    } // }}}
); // }}}

// vi:foldmethod=marker
