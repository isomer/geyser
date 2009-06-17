#!/usr/bin/env python

class TruncatedMessage(Exception):
	pass

def decode_dict(msg):
	assert msg[0] == "{",repr(msg)
	msg=msg[1:]
	d={}
	while msg!="" and msg[0] != "}":
		k,msg = decode(msg)
		v,msg = decode(msg)
		d[k]=v
	if msg=="":
		raise TruncatedMessage()
	return d,msg[1:]

def decode_str(msg):
	assert msg[0] == "s",repr(msg)
	l=0
	msg=msg[1:]
	while msg[0] in "0123456789":
		l=l*10 + ord(msg[0])-ord('0')
		msg=msg[1:]
	if msg=="":
		raise TruncatedMessage()
	return msg[1:l+1],msg[l+1:]
	
def decode_int(msg):
	assert msg[0] == "i",repr(msg)
	v=0
	msg=msg[1:]
	while msg!="" and msg[0] in "0123456789":
		v=v*10+ord(msg[0])-ord('0')
		msg=msg[1:]
	return v,msg

def decode_list(msg):
	assert msg[0] == "[",repr(msg)
	l=[]
	msg=msg[1:]
	while msg!="" and msg[0] not in "]":
		v,msg = decode(msg)
		l.append(v)
	if msg == "":
		raise TruncatedMessage()
	return l,msg[1:]

decodes = {
	"{" : decode_dict,
	"s" : decode_str,
	"i" : decode_int,
	"[" : decode_list,
}

def decode(msg):
	# Skip whitespace
	while msg.startswith("\n") or msg.startswith("\r"):
		msg=msg[1:]
	if msg=="":
		raise TruncatedMessage()
	return decodes[msg[0]](msg)

def encode(d):
	if type(d)==type({}):
		x = [(encode(a)+encode(b)) for (a,b) in d.items()]
		return ("{" 
			+ reduce(lambda a,b:a+b,x,"")
			+ "}")
	if type(d)==type([]):
		if d==[]:
			return "[]"
		return "[" + reduce(lambda a,b:a+b,[encode(x) for x in d]) + "]"
	if type(d)==type(1) or type(d) == type(1L):
		return "i"+str(d)
	if type(d)==type(""):
		return "s"+str(len(d))+":"+d
	assert False,(type(d),d,d.__class__)


if __name__=="__main__":
	d1=decode("{s2:hi[i123i456]s5:hello[i4444i3333]}")
	e1=encode(d1[0])
	d2=decode(e1)
	e2=encode(d2[0])
	print d1,e1,d2,e2
	e=encode(["Fish"])
	print repr(e)
	print decode(e)[0]
	try:
		d2=decode(e1[:-1])
		print d2
	except TruncatedMessage:
		pass

