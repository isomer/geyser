#!/usr/bin/python
import os
import socket
import OpenSSL.SSL


def verify_cb(conn, cert, errnum, depth, ok):
# This obviously has to be updated
	print 'Got certificate: %s' % cert.get_subject()
	if cert.has_expired():
		print "Certificate has expired"
		return False # This cert is not good.
	else:
		print "Certificate is fresh"
	print " DIgest:",`cert.digest("sha256")`
	# Ignore "ok", just return ok for all certs that we validate
	return True # Certificate is OK

ctx = OpenSSL.SSL.Context(OpenSSL.SSL.TLSv1_METHOD)
ctx.set_options(OpenSSL.SSL.OP_NO_SSLv2)
ctx.set_verify(OpenSSL.SSL.VERIFY_PEER|OpenSSL.SSL.VERIFY_FAIL_IF_NO_PEER_CERT, verify_cb)
ctx.use_privatekey_file("server.key")
ctx.use_certificate_file("server.crt")

def wrap_server(fd):
	return OpenSSL.SSL.Connection(ctx,socket.socket(fd))

def wrap_client(fd):
	return OpenSSL.SSL.Connection(ctx,socket.socket(fd))
