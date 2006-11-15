"""
The widget that displays the GM's toolbox.
"""
import mimetypes
import md5
import re

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from PIL import Image

from twisted.python.util import sibpath

from nevow import loaders, athena, rend, inevow, url, tags as T, flat, page

from webby import tabs, util, theGlobal, data
from webby.data import File

import formal

RESOURCE = lambda f: sibpath(__file__, f)

# load our own mime-types, because the set python comes with by default is
# *pathetic*
mimetypes.init([RESOURCE('mime.types'), ])

# map MIME types to image filename. This is a list because the
# matches are meant to be done in order.  Thus, the most generic
# icon is the last one.
mimeIcons = [('image/.*', 'image-x-generic.png'), # {{{
             ('audio/.*', 'audio-x-generic.png'),
             ('video/.*', 'video-x-generic.png'),
             ('text/x-.*sh', 'application-x-executable.png'),
             ('text/.*', 'text-x-generic.png'),
             ('application/java-archive', 'application-x-executable.png'),
             ('application/x-msdos-program', 'application-x-executable.png'),
             ('application/x-msi', 'application-x-executable.png'),
             ('application/zip', 'package-x-generic.png'),
             ('application/x-tar', 'package-x-generic.png'),
             ('application/octet-stream', 'applications-system.png'),
             ('.*', 'applications-system.png'),
             ] # }}}

def iconForMimeType(mimeType):
    """Return the icon filename for a given mimeType string"""
    for pattern, filename in mimeIcons:
        if re.match(pattern, mimeType):
            return filename
    assert 0, "The final pattern in mimeIcons should always match something, so we should not get here."

class ChooserIcon(page.Element):
    docFactory = loaders.xmlfile(RESOURCE('elements/ChooserIcon'))
    def __init__(self, user, fileitem, *a, **kw):
        super(ChooserIcon, self).__init__(*a, **kw)
        self.fileitem = fileitem
        self.user = user

    def chooserIcon(self, req, tag):
        fi = self.fileitem
        tag.fillSlots('filename', fi.filename)
        if fi.mimeType.startswith(u'image/') and fi.thumbnail is not None:
            tag.fillSlots('icon', '/files/%s/thumb' % (fi.md5,))
        else:
            tag.fillSlots('icon', '/images/%s' % (iconForMimeType(fi.mimeType),))
        return tag

    page.renderer(chooserIcon)

class UploadBox(athena.LiveElement):
    docFactory = loaders.xmlfile(RESOURCE('elements/UploadBox'))
    def __init__(self, user, *a, **kw):
        super(UploadBox, self).__init__(*a, **kw)
        self.user = user

class GMTools(tabs.TabsElement):
    def __init__(self, user, *a, **kw):
        super(GMTools, self).__init__(*a, **kw)
        self.user = user
        uploadbox = UploadBox(self.user)
        uploadbox.setFragmentParent(self)

        self.addInitialTab(u'images', u'Images & Sounds', uploadbox)

class UploadPage(formal.ResourceMixin, rend.Page):
    """
    Perform file uploads which will be stored in the Axiom store.
    """
    addSlash = True
    docFactory = loaders.xmlfile(RESOURCE('upload.xhtml'))
    def __init__(self, user, *a, **kw):
        formal.ResourceMixin.__init__(self, *a, **kw)
        rend.Page.__init__(self, *a, **kw)
        self.user = user

    def form_upload(self, ctx):
        f = formal.Form()
        f.addField('file', formal.File())
        f.addAction(self.saveFile)
        return f

    def saveFile(self, ctx, form, data):
        """Receive the file and drop it into the Axiom box."""
        db = theGlobal['dataService'].store
        filename, filedata = data['file']

        # when the file was not successfully uploaded, filename==u''
        if len(filename) > 0:
            readdata = filedata.read()
            m = unicode(md5.md5(readdata).hexdigest())
            # make sure that a particular file can only be uploaded once
            if db.findFirst(File, File.md5==m) is None:
                def _newFile():
                    mimeType = unicode(mimetypes.guess_type(filename)[0])
                    newfile = File(store=db,
                            filename=filename,
                            data=readdata,
                            md5=m,
                            mimeType=mimeType,
                            user=self.user,
                            )

                    # now thumbnail it
                    if mimeType.startswith('image/'):
                        # PIL can't thumbnail every identifiable kind of
                        # image, so just punt if it fails to update.
                        try:
                            filedata.seek(0)
                            thumb = Image.open(filedata)
                            thumb.thumbnail((48,48), Image.ANTIALIAS)
                            _tempfile = StringIO()
                            thumb.save(_tempfile, 'PNG')
                            _tempfile.seek(0)
                            newfile.thumbnail = _tempfile.read()
                        except IOError:
                            pass
                db.transact(_newFile)


    def render_chooser(self, ctx, _):
        db = theGlobal['dataService'].store
        _fileitems = db.query(data.File, data.File.user==self.user, 
                sort=data.File.filename.ascending)
        return [ChooserIcon(self.user, fi) for fi in _fileitems]
