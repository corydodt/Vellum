import re

try:
    from cStringIO import cStringIO as StringIO
except ImportError:
    from StringIO import StringIO

from PIL import Image, ImageDraw

BLACK = 0
TRANS = 1


def newTransparentImage(w, h):
    """
    @return a string containing the PNG bytes of a black image with
    the specified dimensions.
    """
    i = Image.new('P', (w, h), TRANS)
    return saveObscurement(i)

def newBlackImage(w, h):
    """
    @return a string containing the PNG bytes of a black image with
    the specified dimensions.
    """
    i = Image.new('P', (w, h), BLACK)
    return saveObscurement(i)

def saveObscurement(image):
    """
    Return a 1-bit PNG byte string from the PIL image
    """
    output = StringIO()
    output.name = '__obscurement.png'
    image.save(output, optimize=True, transparency=TRANS, bits=1)
    output.seek(0)

    return output.read()

def renderTransparency(origbytes, pathdata):
    """
    @return a string representing the transparency, first superimosing the
    path as a cutout on the original.
    """
    input = StringIO(origbytes)
    i = Image.open(input)

    path = parseSVGPath(pathdata)
    di = ImageDraw.Draw(i)
    di.polygon(path, outline=None, fill=TRANS)
    return saveObscurement(i)

NUMBERFINDER = re.compile(r'(?:\b|[^.\d])([.\d]+)(?:\b|[^.\d])')


def parseSVGPath(pathstring):
    """
    @return a sequence of 2-tuples (x,y) from the given string, which is a
    path, as represented by SVG's <path> or <clippath> 'd' attribute.
    """
    parts = NUMBERFINDER.findall(pathstring)
    assert (len(parts) % 2) == 0, "Path string does not contain even number of x's and y's"
    r = []
    while parts:
        x = parts.pop(0)
        y = parts.pop(0)
        r.append(tuple(map(float, (x,y))))
    return r
