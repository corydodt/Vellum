# define our in-memory test store
from axiom import store

from webby import theGlobal, data

def testUser(st):
    return data.User(store=st, 
            email=u'woot@woot.com', nick=u'woot', password=u'ninjas')

def testFileMeta(st):
    testFileData = data.FileData(store=st,
    data=(
"""iVBORwoaCgAAAA1JSERSAAAAZAAAAGQIAgAAAP+AAgMAAAAJcEhZcwAACxMAAAsTAQCanBgAAAAH
dElNRQfWCx0HNiv9/5VxAAAACHRFWHRDb21tZW50APbMlr8AAACfSURBVHja7dAxAQAACAMgtX/n
WcHPByLQSYqbUSBLlixZsmQpkCVLlixZshTIkiVLlixZCmTJkiVLliwFsmTJkiVLlgJZsmTJkiVL
gSxZsmTJkqVAlixZsmTJUiBLlixZsmQpkCVLlixZshTIkiVLlixZCmTJkiVLliwFsmTJkiVLlgJZ
smTJkiVLgSxZsmTJkqVAlixZsmTJUiBL1rcFz/EDxVmyyQcAAAAASUVORK5CYII="""
    ).decode('base64'))
    return data.FileMeta(store=st, 
            data=testFileData,
            filename=u'white100.png',
            mimeType=u'image/png',
            md5=u'c2d8ac97a07cbf785d2e4d7dbf578d2c',
            width=100,
            height=100)

def cleanStore():
    testStore = store.Store()
    theGlobal['database'] = testStore

    return testStore
