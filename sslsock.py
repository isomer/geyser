#!/usr/bin/python
# This file has several security issues.  For instance, key's are probably 
# hanging around in memory.  But this is a P2P client.  If keys end up in swap
# or hanging around in memory, it's not the worlds most scary exploit.  
# The key is mostly used to prevent DPI boxes from poking around in the packets,
# the only "identity" associated with the key is the amount of data people owe
# you (and you owe them), so throwing away the identity is annoying, but not
# earth shattering.
#
# We're not too worried about local system exploits, mostly just keeping out
# communications over the air safe from tampering and rate limiting.
import os
import socket
import OpenSSL.SSL
import OpenSSL.crypto
import time
import random

preferred_keytype = OpenSSL.crypto.TYPE_RSA
preferred_keylen  = 2048
keyfile = "server.key"
certfile = "server.crt"


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

if not os.path.exists(keyfile):
	# Create a key
	pkey = OpenSSL.crypto.PKey()
	pkey.generate_key(preferred_keytype,preferred_keylen)

	buf=OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, pkey)
	f = open(keyfile, "w")
	f.write(buf)
	f.close()
else:
	pkey = OpenSSL.crypto.load_privatekey(
			OpenSSL.crypto.FILETYPE_PEM,
			open(keyfile,"r").read())

ctx.use_privatekey(pkey)

if not os.path.exists(certfile):
	cert = OpenSSL.crypto.X509()
 	cert.set_serial_number(long('%i%04i' % (time.time() * 1000, 
 						random.randint(0, 9999)))) 
	cert.gmtime_adj_notBefore(0) 
	# Your identity exists for 10 years maximum
 	cert.gmtime_adj_notAfter(10 * 60 * 60 * 24 * 365) 
	# This can possibly be used to fingerprint the connection, so
	# Consider changing it.
	cert.get_subject().CN = '*' 
 	cert.get_subject().O = 'Geyser' 
 	cert.get_issuer().CN = 'Geyser' 
 	cert.get_issuer().O = 'Self-Signed' 
 	cert.set_pubkey(pkey) 
 	cert.sign(pkey, 'sha256') 

	buf=OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
	f = open(certfile, "w")
	f.write(buf)
	f.close()
else:
	cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, 
			open(certfile,"r").read())
ctx.use_certificate(cert)

def wrap_server(fd):
	return OpenSSL.SSL.Connection(ctx,fd)

def wrap_client(fd):
	return OpenSSL.SSL.Connection(ctx,fd)
