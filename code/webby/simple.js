
// import Nevow.Athena
// import Divmod

Simple.SimpleFrag = Nevow.Athena.Widget.subclass('Simple.SimpleFrag');
Simple.SimpleFrag.methods(
    function clicked(self, node, event) {
        if (event.keyCode == 13)
        {
            var input = Nevow.Athena.FirstNodeByAttribute(node,
                'class', 'chatentry')
            self.callRemote("typed", input.value);
        }
        return false;
    }
)
