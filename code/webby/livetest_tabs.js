// import Nevow.Athena.Test
Tabby.Tests.TestTabs = Nevow.Athena.Test.TestCase.subclass("Tabby.Tests.TestTabs");
Tabby.Tests.TestTabs.methods(
    function test_initialTabId(self) {
        var d = self.callRemote("newTabWidget", 'woop', 'Woop');
        d.addCallback(
            function(wi) { return self.addChildWidgetFromWidgetInfo(wi); }
            );
        d.addCallback(
            function(tabs) { self.assertEqual(tabs.activeTabId(), 'woop'); }
            );
        return d;
    },

    function test_initialTabIdAndContent(self) {
        var d = self.callRemote("newTabWidget", 'woop', 'Woop', 
            '<div xmlns="http://www.w3.org/1999/xhtml"><b>Content</b></div>');
        d.addCallback(
            function(wi) { return self.addChildWidgetFromWidgetInfo(wi) }
            );
        d.addCallback(
            function(tabs) {
                var pane = tabs.getPaneForId('woop');
                self.assertEqual(pane.innerHTML.search('<b>Content</b>'), 42);
                }
            );
        return d;
    }
)
