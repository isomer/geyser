#!/usr/bin/python
import random
import sets

blocks = [ "ABC","DEF","GHI","JKL","MNO","PQR","STU","VWX","YZ " ]

def debug(*args):
	#print "".join(map(str,args))
	pass

def xor(b1,b2):
	return "".join([chr(ord(c1)^ord(c2)) for c1,c2 in zip(b1,b2)])

def block_generator(blocks):
	while 1:
		degree = random.randint(1,len(blocks))
		indexes=sets.Set()
		for i in range(degree):
			while 1:
				r = random.randint(0,len(blocks)-1)
				if r not in indexes:
					indexes.add(r)
					break
		body="\x00"*len(blocks[0])
		for i in indexes:
			body=xor(body,blocks[i])
		yield (indexes,body)

class Reassemble:
	def __init__(self,blocks):
		self.seen = sets.Set()
		self.staging=[]
		self.done=[]
		self.todo=[]
		self.waiting=sets.Set(range(blocks))

	def pushBlock(self,(ind,block)):
		if not ind in self.seen:
			self.todo.append((ind,block))
			return self.runTodo()
		else:
			print "Useless block"

	def processBlock(self,(ind,block),staging):
		newstaging=[]
		while staging!=[]:
			(sind,sblock)=staging.pop()
			nind = ind.symmetric_difference(sind)
			# Produces a more complex block
			if len(nind) >= len(sind) and len(nind) >= len(ind):
				newstaging.append((sind,sblock))
				continue
			# Been here, done that.
			if nind in self.seen:
				debug("",ind,"x",sind," -- seen")
				return newstaging+[(sind,sblock)]+staging
				#newstaging.append((sind,sblock))
				#continue
			nblock = xor(block,sblock)
			self.todo.append((nind,nblock))
			if len(sind) < len(ind):
				debug("",ind,"x",sind,"=>",nind,sind)
				ind,block = sind,sblock
			else:
				debug("",ind,"x",sind,"=>",ind,nind)
		staging=newstaging+[(ind,block)]
		staging.sort(lambda (a,b),(c,d):cmp(len(a),len(c)) or cmp(list(a),list(c)))
		return staging

	def runTodo(self):
		while self.todo!=[]:
			self.todo.sort(lambda (a,b),(c,d):cmp(len(a),len(b)))
			(ind,block) = self.todo.pop(0)
			if ind in self.seen:
				continue
			if len(ind) == 1:
				self.done.append((ind,block))
				bnum = ind.copy().pop()
				self.waiting.remove(bnum)
				print "Found block:",bnum,repr(block),"Waiting on:",self.waiting
				if len(self.waiting)==0:
					return True
			self.seen.add(ind)
			debug("Considering",ind)
			self.staging=self.processBlock((ind,block),self.staging)
		debug("Staging:",[x for (x,y) in self.staging])
				

if __name__=="__main__":
	#random.seed(1)
	r =Reassemble(len(blocks))
	c=0
	for i in block_generator(blocks):
		c=c+1
		print "Recieved encoded block",c
		if r.pushBlock(i):
			break
