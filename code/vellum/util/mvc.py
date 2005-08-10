"""An observer technique that allows tracing.  That is, 
1) An observed thing--called a Noumenon--publishes events to as many
   observers as call registerObserver on it
2) Assignments cannot be made directly on the Noumenon.  Instead, they must be
   made through an Arbiter.
3) Assignments made to the Arbiter are published to all observers.
4) An Arbiter has a descriptive tag.  It publishes its tag to observers.
   Thus, they can tell who made the assignment by examining the tag.
   (A tag can be any object, but is most likely a string.)
5) To get an Arbiter, an observer calls getArbiter() on the Noumenon.
"""
class Noumenon:
    """
    Something with observable properties.  AKA the "Model".
    Use registerObserver to make an instance the recipient of change events.
    Observable Phenomena are given by name in __phenomena__
    To understand the name, read your Kant, or try here: 
        http://en.wikipedia.org/wiki/Noumenon
    Kant is wrong though, noumena derived from this can be introspected. ;-)
    """
    def __init__(self):
        self.__dict__['observers'] = []

    def registerObserver(self, observer):
        self.observers.append(observer)

    def getArbiter(self, tag):
        """Return an object which accepts assignments to phenomena"""
        return Arbiter(tag, self)

    def __setattr__(self, name, value):
        raise RuntimeError("Assignments must be made through an Arbiter.")



class Arbiter:
    def __init__(self, tag, noumenon):
        self.__dict__['noumenon'] = noumenon
        self.tag = tag

    def __setattr__(self, name, value):
        n = self.noumenon
        old = getattr(n, name, None)

        if name in n.__phenomena__:
            n.__dict__[name] = value
            # call foo_changed(model, old, new) on observers
            for obs in n.observers:
                notification = getattr(obs, '%s_changed' % (name,), None)
                if notification is not None:
                    notification(self.tag, n, old, value)
            return
        self.__dict__[name] = value

    def __getattr__(self, name):
        if name in self.noumenon.__phenomena__:
            return getattr(self.noumenon, name)
        raise AttributeError(name)


def test():
    output = []
    class Hork(Noumenon):
        __phenomena__ = ['foo', 'bar']

    class Director:
        def __init__(self, model):
            model.registerObserver(self)
            self.model = model.getArbiter('director')
        def foo_changed(self, tag, model, old, new):
            if tag is 'director':
                return
            if old == new:
                return
            output.append(('foo', old, new, tag))
            self.model.bar = 2
        def bar_changed(self, tag, model, old, new):
            output.append(('bar', old, new, tag))


    h = Hork()
    arbiter = h.getArbiter('__main__')
    d = Director(h)

    try: 
        h.foo = 1
    except RuntimeError, e:
        pass
    else:
        assert 0, "should not be able to assign to h.foo"

    try:
        print h.foo
    except AttributeError, e:
        pass
    else:
        assert 0, "h.foo should raise an AttributeError"

    arbiter.foo = 1
    assert output.pop(0) == ('foo', None, 1, '__main__')
    assert output.pop(0) == ('bar', None, 2, 'director')
    arbiter.foo = 2
    assert output.pop(0) == ('foo', 1, 2, '__main__')
    assert output.pop(0) == ('bar', 2, 2, 'director')
    arbiter.bar = 1
    assert output.pop(0) == ('bar', 2, 1, '__main__')

    d.model.foo = 1
    assert len(output) == 0
    print 'all passed'

if __name__ == '__main__':
    test()
