try:
    from cStringIO import cStringIO as StringIO
except ImportError:
    from StringIO import StringIO

from PIL import Image

BLACK = 0
TRANS = 1


def newBlackImage(w, h):
    """
    @return a string containing the PNG bytes of a black image with
    the specified dimensions.
    """
    i = Image.new('P', (w, h), BLACK)

    output = StringIO()
    output.name = '__obscurement.png'
    i.save(output, optimize=True, transparency=TRANS, bits=1)

    output.seek(0)

    return output.read()
