"""
Do insane shit to make gtk import on Windows even when the PATH is broked.
"""

import sys, os
# hack taken from <http://www.livejournal.com/users/glyf/7878.html>
def getGtkPath():
    import _winreg
    subkey = 'Software/GTK/2.0/'.replace('/','\\')
    path = None
    for hkey in _winreg.HKEY_LOCAL_MACHINE, _winreg.HKEY_CURRENT_USER:
        reg = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, subkey)
        for vname in ("Path", "DllPath"):
            try:
                try:
                    path, val = _winreg.QueryValueEx(reg, vname)
                except WindowsError:
                    pass
                else:
                    return path
            finally:
                _winreg.CloseKey(reg)

if sys.platform == 'win32':
    path = getGtkPath()
    if path is None:
        raise ImportError("Couldn't find GTK DLLs.")
    os.environ['PATH'] += ';'+path.encode('utf8')

## end damn gtk hack

