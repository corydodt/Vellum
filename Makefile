
start:
	hg serve --daemon --port 28080 --pid-file hgserve.pid

stop:
	kill `cat hgserve.pid`
