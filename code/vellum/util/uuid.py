# Credit to Carl Free Jr.
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/213761
import time, random, md5, socket, threading
import sys

lock = threading.RLock()

def uuid( *args ):
    """
    Generates a universally unique ID.
    Any arguments only create more randomness.
    """
    try:
        lock.acquire()
        t = long( time.time() * 1000 )
        r = long( random.random()*100000000000000000L )
        try:
            a = socket.gethostbyname( socket.gethostname() )
        except:
            # if we can't get a network address, just imagine one
            a = random.random()*100000000000000000L
        data = str(t)+' '+str(r)+' '+str(a)+' '+str(args)
        data = md5.md5(data).hexdigest()
        return data
    finally:
        lock.release()


if __name__ == '__main__':
    print uuid("".join(sys.argv))
