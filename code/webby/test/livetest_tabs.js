// import Nevow.Athena.Test
// import Divmod.Runtime
// import Divmod.Defer

XHTMLNS = "http://www.w3.org/1999/xhtml";

RT = Divmod.Runtime.theRuntime;

Tabby.Tests.TestTabs = Nevow.Athena.Test.TestCase.subclass("Tabby.Tests.TestTabs");
Tabby.Tests.TestTabs.methods( // {{{
    /* get a new tabs widget with just a label and id */
    function test_initialTabId(self) { // {{{
        var d = self.callRemote("newTabWidget", 'woop', 'Woop');
        d.addCallback(
            function(wi) { return self.addChildWidgetFromWidgetInfo(wi); }
            );
        d.addCallback(
            function(tabs) { 
                self.assertEqual(tabs.activeTabId(), 'woop'); 
                self.assertEqual(
                        tabs.getHandleForId('woop').innerHTML, 'Woop'); 
                }
            );
        return d;
    }, // }}}

    /* get a new tabs widget with just a label and id, and XHTML content */
    function test_initialTabIdAndContent(self) { // {{{
        var d = self.callRemote("newTabWidget", 'woop', 'Woop', 
            '<div xmlns="' + XHTMLNS + '"><b>Content</b></div>');
        d.addCallback(
            function _(wi) { return self.addChildWidgetFromWidgetInfo(wi); }
            );
        d.addCallback(
            function _(tabs) {
                var pane = tabs.getPaneForId('woop');
                self.assertEqual(pane.innerHTML.search('<b>Content</b>'), 42);
                }
            );
        return d;
    }, // }}}

    /* get a new tabs widget with just a label and id, and widget content */
    function test_initialTabIdAndWidget(self) { // {{{
        var d = self.callRemote("newTabWidgetContainingWidget", 'woop', 'Woop');
        d.addCallback(function _(wi) { 
                return self.addChildWidgetFromWidgetInfo(wi); 
        });
        d.addCallback(function _(tabs) {
                var pane = tabs.getPaneForId('woop');
                self.assertEqual(pane.innerHTML.search('<b>Content</b>'), 140);
        });
        return d;
    }, // }}}

    /* ask the server to call addTab and setTabBody on me */
    function test_addTabSetTab(self) { // {{{
        var d = self.setUp();
        d.addCallback(
            function _(tabs) {
                self.addTabSetTabWidget = tabs;
                d2 = self.callRemote('driveAddTabSetTab');
                d2.addCallback(
                    function _(ignored) {
                        var n = tabs.node;
                        Divmod.debug('test', n.innerHTML);
                        self.assertEqual(n.innerHTML.search('Content</b>'), 297);
                });
                return d2;
        });
        return d;
    }, // }}}

    function addTab(self, id, label) { // {{{
        return self.addTabSetTabWidget.addTab(id, label);
    }, // }}}

    function setTabBody(self, id, content) { // {{{
        return self.addTabSetTabWidget.setTabBody(id, content);
    }, // }}}

    function test_clicked(self) { // {{{
        var d = self.setUp();
        d.addCallback(
            function _(tabs) { 
                tabs.addTab('1', 'One');
                tabs.addTab('2', 'Two');
                self.assertEqual(tabs.activeTabId(), '2');
                var onehandle = RT.firstNodeByAttribute(tabs.node, 'href', '#1');
                tabs.clicked(onehandle);
                self.assertEqual(tabs.activeTabId(), '1');
            });
    }, // }}}

    function test_show(self) { // {{{
        var d = self.setUp();
        d.addCallback(
            function _(tabs) { 
                tabs.addTab('1', 'One');
                tabs.addTab('2', 'Two');
                self.assertEqual(tabs.activeTabId(), '2');
                tabs.show('1');
                self.assertEqual(tabs.activeTabId(), '1');
                }
            );
        return d;
    }, // }}}

    function test_removeTab(self) { // {{{
        var d = self.setUp();
        d.addCallback(
            function _(tabs) {
                tabs.addTab('1', 'One');
                tabs.addTab('2', 'Two');
                var handleNode = RT.firstNodeByAttribute(
                        tabs.node, 'class', 'handles');
                var paneNode = RT.firstNodeByAttribute(
                        tabs.node, 'class', 'panes');
                self.assertEqual(handleNode.childNodes.length, 2);
                self.assertEqual(paneNode.childNodes.length, 2);
                tabs.removeTab('1');
                self.assertEqual(handleNode.childNodes.length, 1);
                self.assertEqual(paneNode.childNodes.length, 1);
                self.assertThrows(
                        Divmod.Runtime.NodeAttributeError,
                        function _() { tabs.show('1'); }
                        );
            });
        return d;
    }, // }}}

    function test_appendToTab(self) { // {{{
        var d = self.setUp();
        d.addCallback(
            function _(tabs) {
                tabs.addTab('1', 'One');
                var p = tabs.getPaneForId('1');
                self.assertEqual(p.innerHTML.length, 0);
                tabs.appendToTab('1', '<span xmlns="' + XHTMLNS + '">Babar</span>');
                self.failUnless(p.innerHTML.search('Babar') >= 0);
                tabs.appendToTab('1', '<p xmlns="' + XHTMLNS + '">Hi</p>');
                self.failUnless(p.innerHTML.search('Hi</p>') >= 0);
            });
        return d;
    }, // }}}

    function test_appendWidgetToTab(self) { // {{{
        var d = self.setUp();
        d.addCallback(
            function _(tabs) {
                tabs.addTab('1', 'One');
                var p = tabs.getPaneForId('1');
                self.assertEqual(p.innerHTML.length, 0);

                var d2 = self.callRemote('newVerySimpleWidget');
                d2.addCallback(function _gotInfo(vswinfo) {
                    var d3 = tabs.appendWidgetInfoToTab('1', vswinfo);
                    d3.addCallback(function _addedWidget(_) {
                        self.failUnless(p.innerHTML.search('Content</b>') >= 0);
                    });
                    return d3;
                });
                return d2;
            });
        return d;
    }, // }}}

    function test_setTabBody(self) { // {{{
        var d = self.setUp();
        d.addCallback(
            function _(tabs) {

                // check the behavior with widgets
                tabs.addTab('1', 'One');
                var p1 = tabs.getPaneForId('1');

                var dw = self.callRemote('newVerySimpleWidget');
                dw.addCallback(function _gotInfo(vswinfo) {
                    var d3 = tabs.setTabBody('1', vswinfo);
                    d3.addCallback(function _addedWidget(_) {
                        self.failUnless(p1.innerHTML.search('Content</b>') >= 0);
                    });
                    return d3;
                });

                // check the behavior with regular content
                tabs.addTab('2', "Two");
                var p2 = tabs.getPaneForId('2');

                var content = 
                    '<span xmlns="http://www.w3.org/1999/xhtml">Regular</span>';
                var dc = tabs.setTabBody('2', content);
                dc.addCallback(function _addedContent(_) {
                    self.failUnless(p2.innerHTML.search('Regular') >= 0);
                });

                return Divmod.Defer.DeferredList([dw, dc], false, true);
            });
        return d;
    }, // }}}

    function setUp(self) { // {{{
        var d = self.callRemote("newTabWidget");
        d.addCallback(
            function _(wi) { return self.addChildWidgetFromWidgetInfo(wi); }
            );
        return d;
    } // }}}
); // }}}

// vi:foldmethod=marker
