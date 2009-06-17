# Based very haavily on BaseHTTPServer
import mainloop
import time

class HTTPError(Exception):
	def __init__(self, code, message):
		self.code = code
		self.message = message

class BaseGeyserHTTPServer:
	def __init__(self, fd, addr):
		self.fd = fd
		self.addr = addr
		self.inbuffer = ""
		self.outbuffer = ""
		self.state = self.parse_requestline
		self.version = (0,9)
		mainloop.addReader(self)

	def readEvent(self):
		self.inbuffer += self.fd.recv(4096)
		try:
			self.state()
		except HTTPError, e:
			self.send_error(e.code,e.message)

	def writeEvent(self):
		ret=self.fd.send(self.outbuffer)
		self.outbuffer = self.outbuffer[ret:]
		if self.outbuffer == "":
			mainloop.delWriter(self)
			if self.close_connection:
				mainloop.delReader(self)
				self.fd.close()

	def fileno(self):
		return self.fd.fileno()

	def rawsend(self,msg):
		if self.outbuffer == "":
			mainloop.addWriter(self)
		self.outbuffer += msg

	def send(self,msg):
		self.body += msg

	def flush(self):
		self.send_header("Content-Length", str(len(self.body)))
		if not self.sent_end_headers:
			self.end_headers()
		self.rawsend(self.body)

	def readline(self):
		if "\r" in self.inbuffer:
			line, self.inbuffer = self.inbuffer.split("\r",1)
			if self.inbuffer.startswith("\n"):
				self.inbuffer=self.inbuffer[1:]
			return line
		return None # We don't have a complete line yet

	def parse_requestline(self):
		self.raw_requestline = self.readline()
		# Have we got the data yet?
		if self.raw_requestline is None:
			return

		self.method = None
		self.version = 0,9
		self.close_connection = 1
		self.body = ""
		self.sent_end_headers=0

		self.headerlist = []

		words = self.raw_requestline.rstrip().split()
		if len(words) == 3:
			(self.command, self.path, version) = words
			if not version.startswith("HTTP/"):
				raise HTTPError(400,"Bad version (%r)" % version)
			version = version.split("/",1)[1]
			version = version.split(".")
			if len(version) != 2:
				raise HTTPError(400,"Bad version (%d)" % version)
			self.version = tuple(map(int,version))
		elif len(words) == 2:
			[self.command, self.path] = words
			self.version = 0,9
		else:
			raise HTTPError(400, "Bad Request (%r)" % self.raw_requestline)
		if version >= (2,0):
			raise HTTPError(505,"Invalid HTTP Version %r" % self.version)
		if version >= (1,1):
			self.close_connection = 0

		self.state = self.parse_headers

		print "Got request line:",repr(words)
		self.state()

	def parse_headers(self):
		while 1:
			line = self.readline()
			if line is None:
				return # Incomplete line
			if line.strip() == "":
				break
			if line[0] in ' \t':
				self.headerlist[-1] += "\n" + line.strip()
			if ":" not in line:
				raise HTTPError(400,"Bad request: Bad header (%r)" % line)
			else:
				self.headerlist.append(line)
		
		self.headerdict=dict([(header.split(":",1)[0].lower(),header.split(":",1)[1].strip()) for header in self.headerlist])
		if self.headerdict.get('connection','').lower() == "close":
			self.close_connection = 1
		elif self.headerdict.get("connection","").lower() == "keep-alive":
			self.close_connection = 0

		print "Headers:",self.headerdict

		mname = "do_" + self.command
		if hasattr(self, mname):
			self.state = getattr(self, mname)
			self.state()
		else:
			raise HTTPError(501, "Unsupported method (%r)" % self.command)

	def send_error(self, code, message=None):
		if code in self.responses:
			short, long = self.responses[code]
		else:
			short, long = '???', '???'
		message = message or long
		if self.version > (0,9):
			self.rawsend("HTTP/%d.%d %03d %s\r\n" % (self.version+(code,short)))
		self.send_header('Server', "Geyser v1.0")
		self.send_header('Data', self.date_time_string())
		self.send_header('Connection', 'close')
		self.send("<h1>%s</h1>" % message)
		self.flush()

	def send_header(self, keyword, value):
		"""Send a MIME header."""
		if self.version != (0,9):
		    self.rawsend("%s: %s\r\n" % (keyword, value))
		    
		if keyword.lower() == 'connection':
		    if value.lower() == 'close':
			self.close_connection = 1
		    elif value.lower() == 'keep-alive':
			self.close_connection = 0

	def end_headers(self):
		"""Send the blank line ending the MIME headers."""
		if self.version != (0,9):
		    self.rawsend("\r\n")
		self.sent_end_headers = 1

	def date_time_string(self, timestamp=None):
		"""Return the current date and time formatted for a message
		header."""
		if timestamp is None:
		    timestamp = time.time()
		year, month, day, hh, mm, ss, wd, y, z = time.gmtime(timestamp)
		s = "%s, %02d %3s %4d %02d:%02d:%02d GMT" % (
			self.weekdayname[wd],
			day, self.monthname[month], year,
			hh, mm, ss)
		return s

	# Table mapping response codes to messages; entries have the
	# form {code: (shortmessage, longmessage)}.
	# See RFC 2616.
        responses = {
		100: ('Continue', 'Request received, please continue'),
		101: ('Switching Protocols',
			'Switching to new protocol; obey Upgrade header'),

		200: ('OK', 'Request fulfilled, document follows'),
		201: ('Created', 'Document created, URL follows'),
		202: ('Accepted',
			'Request accepted, processing continues off-line'),
		203: ('Non-Authoritative Information', 'Request fulfilled from cache'),
		204: ('No Content', 'Request fulfilled, nothing follows'),
		205: ('Reset Content', 'Clear input form for further input.'),
		206: ('Partial Content', 'Partial content follows.'),

		300: ('Multiple Choices',
			'Object has several resources -- see URI list'),
		301: ('Moved Permanently', 'Object moved permanently -- see URI list'),
		302: ('Found', 'Object moved temporarily -- see URI list'),
		303: ('See Other', 'Object moved -- see Method and URL list'),
		304: ('Not Modified',
			'Document has not changed since given time'),
		305: ('Use Proxy',
			'You must use proxy specified in Location to access this '
			'resource.'),
		307: ('Temporary Redirect',
			'Object moved temporarily -- see URI list'),

		400: ('Bad Request',
			'Bad request syntax or unsupported method'),
		401: ('Unauthorized',
			'No permission -- see authorization schemes'),
		402: ('Payment Required',
			'No payment -- see charging schemes'),
		403: ('Forbidden',
			'Request forbidden -- authorization will not help'),
		404: ('Not Found', 'Nothing matches the given URI'),
		405: ('Method Not Allowed',
			'Specified method is invalid for this server.'),
		406: ('Not Acceptable', 'URI not available in preferred format.'),
		407: ('Proxy Authentication Required', 'You must authenticate with '
			'this proxy before proceeding.'),
		408: ('Request Timeout', 'Request timed out; try again later.'),
		409: ('Conflict', 'Request conflict.'),
		410: ('Gone',
			'URI no longer exists and has been permanently removed.'),
		411: ('Length Required', 'Client must specify Content-Length.'),
		412: ('Precondition Failed', 'Precondition in headers is false.'),
		413: ('Request Entity Too Large', 'Entity is too large.'),
		414: ('Request-URI Too Long', 'URI is too long.'),
		415: ('Unsupported Media Type', 'Entity body in unsupported format.'),
		416: ('Requested Range Not Satisfiable',
			'Cannot satisfy request range.'),
		417: ('Expectation Failed',
			'Expect condition could not be satisfied.'),

		500: ('Internal Server Error', 'Server got itself in trouble'),
		501: ('Not Implemented',
			'Server does not support this operation'),
		502: ('Bad Gateway', 'Invalid responses from another server/proxy.'),
		503: ('Service Unavailable',
			'The server cannot process the request due to a high load'),
		504: ('Gateway Timeout',
			'The gateway server did not receive a timely response'),
		505: ('HTTP Version Not Supported', 'Cannot fulfill request.'),
	}

	weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

	monthname = [None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
			'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

class GeyserHTTPServer(BaseGeyserHTTPServer):
	def do_GET(self):
		if self.version > (0,9):
			self.rawsend("HTTP/%d.%d %03d %s\r\n" % (self.version+(200,"Ok")))
		self.send_header('Server', "Geyser v1.0")
		self.send_header('Data', self.date_time_string())
		self.send("<h1>YAY!</h1>")
		self.flush()

