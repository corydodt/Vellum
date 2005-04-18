

class Viewed:
    """The background and everything on it.
    Abstraction to provide a thing which can be slid around in the display,
    zoomed, etc.
    """
    def __init__(self):
        self.rect = 0,0
        self.characters = []

        pygame.display.set_caption('SeeFantasy')
        self.screen = pygame.display.set_mode((320,240))


    def addCharacter(self, image, left, top, name):
        self.characters.append((image, left, top, name))

    def _getMapInfo(self):
        for fi in self.infos:
            if fi['type'] == 'map':
                return fi

    def setMap(self, image):
        self.map = image
        rect = self.map.get_rect()

        self.screen.blit(self.map, (0,0))

    def clearObscurement(self):
        pass

    def update(self):
        pygame.display.get_surface().blit(self.map, self.rect)

    def push(self, (right, up)):
        new = self.rect.move((right, up))
        FIXME


class Game:
    def __init__(self, options):
        self.options = options
        pygame.init()

        self.view = Viewed()

        self._loop = task.LoopingCall(self.pump).start(1.0/options['fps'])
        
        self.pbobject = None

        self.files = []
        self.fs = Filesystem('downloads', mkdir=1)

    def _eb(self, error):
        print 'error:'
        return log.err()


    def pump(self):
        try:
            pygame.display.flip()
            for e in pygame.event.get():
                self.dispatch_event(e)
        except Exception, e:
            log.err(e)

    def __getattr__(self, name):
        if name.startswith('handle_'):
            return self.handle_default
        raise AttributeError(name)

    def handle_default(self, event):
        pass

    def handle_QUIT(self, event):
        reactor.stop()

    def handle_KEYUP(self, event):
        k = event.key
        if pygame.key.name(k) == 'q' or k == locals.K_ESCAPE:
            self.handle_QUIT(event)
        elif k == locals.K_LEFT:
            self.view.push((-20, 0))
        elif k == locals.K_RIGHT:
            self.view.push((20, 0))
        elif k == locals.K_UP:
            self.view.push((0, 20))
        elif k == locals.K_DOWN:
            self.view.push((0, -20))

    def dispatch_event(self, event):
        if event.type == locals.KEYDOWN:
            self.handle_KEYDOWN(event)
        if event.type == locals.KEYUP:
            self.handle_KEYUP(event)
        elif event.type == locals.MOUSEMOTION:
            self.handle_MOUSEMOTION(event)
        elif event.type == locals.MOUSEBUTTONUP:
            self.handle_MOUSEBUTTONDOWN(event)
        elif event.type == locals.MOUSEBUTTONUP:
            self.handle_MOUSEBUTTONUP(event)
        elif event.type == locals.QUIT:
            self.handle_QUIT(event)

