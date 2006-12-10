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

    function test_checkForDrop(self) { // {{{
        var d = self.setUp();
        var mymap = null;
        d.addCallback(function _(map) {
            mymap = map;
            return self.callRemote("newMapWidgetInContainer");
        });
        d.addCallback(function _(info) { 
            return self.addChildWidgetFromWidgetInfo(info);
        });
        d.addCallback(function _(irc) {
            try {
                // just put the map node into the container, bypassing irc
                // login
                irc.node.appendChild(mymap.node);
                // monkey patch the ChatEntry in the container with our mock one.
                irc.childWidgets[2] = SVGMap.Tests.MockChatEntry();

                var ev = MockEvent(mymap.node);

                /* check that non-image droppables will be ignored */
                window.droppable = document.createElement('foop');
                window.droppable.className = 'chooserIcon';
                var ret = mymap.checkForDrop(ev);
                self.assertEqual(ret, undefined);

                /* check that droppables with different classes will be ignored */
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

                /* check that nothing happens when the map is already set */
                var image = document.createElementNS(SVGNS, 'image');
                image.setAttribute('vellum:name', 'map-background');
                mymap.node.appendChild(image);
                var ret = mymap.checkForDrop(ev);
                self.assertEqual(ret, undefined);

            } finally {
                window.droppable = undefined;
            }
        });
        return d;
    }, // }}}

    /* test that setMapBackground can set up the SVG widgets when it gets
       a BackgroundImage widget from the server
     */
    function test_setMapBackground(self) { // {{{
        var d = self.setUp();
        var mymap = null;
        d.addCallback(function _(map) {
            mymap = map;
            return self.callRemote("requestSetMapBackground");
        });
        d.addCallback(function _(info) { 
            return mymap.setMapBackground(info);
        });
        d.addCallback(function _(ignored) {
            self.assertEqual(mymap.node.getAttribute('width'), '100');
            self.assertEqual(mymap.node.getAttribute('height'), '100');
            var bgnode = mymap.firstNodeByAttribute('vellum:name', 
                    'map-background');
            self.assertEqual(
                    bgnode.getAttributeNS(XLINKNS, 'href'), 
                    '/files/c2d8ac97a07cbf785d2e4d7dbf578d2c');
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
