#!/usr/bin/env python
import hashlib
import os
import encoder
import math
import utils
import time

import sys # DEBUG

networkid = hashlib.new("sha256","fount").digest()
events=[]

def toStr(x):
	return x.encode("hex")

def distance(x,y):
	assert type(x)==type("")
	assert type(y)==type("")
	return long(x.encode("hex"),16)^long(y.encode("hex"),16)

class SearchNode:
	def __init__(self,kademlia,dst,k,continuation):
		self.kademlia=kademlia
		self.dst=dst
		self.k=k
		self.continuation=continuation
		self.shortlist=utils.SortedList(
			lambda a,b:cmp(distance(dst,a),distance(dst,b)))
		self.donelist=[]
		self.waitlist=[]
		
		for i in self.kademlia.get_local_close_nodes(dst,k):
			self.addNode(i)

	def addNode(self,node):
		assert node!=""
		if node in self.shortlist:
			return
		if len(self.shortlist) < self.k:
			self.shortlist.append(node)
			self.waitlist.append(node)
			self.kademlia.send_find_node(node,
					self.dst,
					self.k,
					self.found_node)
		elif distance(self.shortlist[0],self.dst) \
				> distance(node, self.dst):
			self.shortlist.append(node)
			self.waitlist.append(node)
			self.kademlia.send_find_node(node,
					self.dst,
					self.k,
					self.found_node)
			# Get rid of the worst
			self.shortlist.pop(0)

	def found_node(self,pkt):
		nodes = pkt["nodes"]
		src = pkt["src"]
		assert self.waitlist!=[]
		if src in self.waitlist:
			self.waitlist.remove(src)
		for i in nodes:
			assert i!=""
			self.addNode(i)
		if self.waitlist==[]:
			self.continuation(self.shortlist)

class SearchValue:
	def __init__(self,kademlia,key,k,continuation):
		self.kademlia=kademlia
		self.key=key
		self.khash = hashlib.new("sha256",self.key).digest()
		self.k=k
		self.continuation=continuation
		self.shortlist=utils.SortedList(
			lambda a,b:cmp(distance(self.khash,a),distance(self.khash,b)))
		self.donelist=[]
		self.waitlist=[]
		self.results=[]
		
		for i in self.kademlia.get_local_close_nodes(self.khash,k):
			self.addNode(i)

	def addNode(self,node):
		assert node!=""
		if node in self.shortlist:
			return
		if len(self.shortlist) < self.k:
			self.shortlist.append(node)
			self.waitlist.append(node)
			self.kademlia.send_find_value(node,
					self.key,
					self.k,
					self.found_node)
		elif distance(self.shortlist[0],self.khash) \
				> distance(node, self.khash):
			self.shortlist.append(node)
			self.waitlist.append(node)
			self.kademlia.send_find_node(node,
					self.key,
					self.k,
					self.found_node)
			# Get rid of the worst
			self.shortlist.pop(0)

	def addResult(self,result):
		for i in self.results:
			if i["value"] == result["value"] \
					and i["from"] == result["from"]:
				i["expire"]=max(i["expire"],result["expire"])
				return
		else:
			self.results.append(result)

	def found_node(self,pkt):
		assert self.waitlist!=[]
		nodes = pkt["nodes"]
		for i in pkt["results"]:
			self.addResult(i)
		src = pkt["src"]
		if src in self.waitlist:
			self.waitlist.remove(src)
		for i in nodes:
			assert i!=""
			self.addNode(i)
		if self.waitlist==[]:
			self.continuation(self.results)

class Kademlia:
	def __init__(self):
		self.me = hashlib.new("sha256",os.urandom(8)).digest()
		self.buckets={}
		self.store={}
		self.callbacks={}
		self.k=10
		self.store={}
		self.maxexpire=86400 # We'll at maximum keep something 1 day
		self.defexpire=3600

	def getNewId(self):
		return os.urandom(8)

	def recv_ping(self,src,pkt):
		self.send(src,"PONG",pkt)

	def recv_store(self,src,pkt):
		self.store[pkt["key"]]=\
			self.store.get(pkt["key"],[]) \
			+[{ 
				"expire" : pkt["expire"]+time.time(),
				"value" : pkt["value"],
				"from" : src,
			}]

	def send_store_value(self,node,key,value,expire=None):
		if expire is None:
			expire = self.defexpire
		self.send(node,"STORE_VALUE",{
				"key" : key,
				"value" : value,
				"expire" : expire,
			})

	def recv_find_value(self,src,pkt):
		self.send(src,"FOUND_VALUE",
			{ 	
			  "id" : pkt["id"],
			  "key" : pkt["key"],
			  "results"  : [
				{
					"value":d["value"],
					"expire":int(d["expire"]-time.time()),
					"from":d["from"],
			 	}
				for d in self.store.get(pkt["key"],[])],
			  "nodes" : list(self.get_local_close_nodes(
					hashlib.new("sha256",pkt["key"]).digest(),
					pkt["k"])),
			})


	def get_local_close_nodes(self,node,k):
		# There is a nicer algorithm, we can tell when we can stop
		# looking at buckets for instance
		best=utils.SortedList(
			lambda a,b:cmp(distance(a,node),distance(b,node)))
		for i in self.buckets:
			for j in self.buckets[i]:
				if best==[] or distance(node,j) < distance(node,best[0]):
					best.append(j)
					if len(best)>k:
						best=best[1:]
		return best

	def recv_find_node(self,src,pkt):
		best = list(self.get_local_close_nodes(pkt["node"],pkt["k"]))
		self.send(src,"FOUND_NODE",{"id":pkt["id"],"nodes":best})

	def recv_found_value(self,src,pkt):
		if pkt["id"] in self.callbacks:
			self.callbacks[pkt["id"]](pkt)
			del self.callbacks[pkt["id"]]

	def iter_find_node(self,dst,k,continuation):
		SearchNode(self,dst,k,continuation)

	def iter_store_value(self,key,value,continuation):
		SearchNode(self,hashlib.new("sha256",key).digest(),self.k,
			lambda nodes:self.iter_store_value_cb(
				key,value,continuation,nodes))

	def iter_store_value_cb(self,key,value,continuation,nodes):
		for node in nodes:
			self.send_store_value(node,key,value)
		continuation()

	def iter_find_value(self,key,continuation):
		SearchValue(self,key,self.k, continuation)

	def send_find_value(self, node, key, k, continuation):
		id=self.getNewId()
		self.callbacks[id]=continuation
		self.send(node,"FIND_VALUE", {
				"k" : k,
				"key" : key,
				"id" : id,
			})

	def send_find_node(self,node,dst,k,continuation):
		assert type(dst) == type("")
		assert type(k) == type(1)
		assert node!=""
		id=self.getNewId()
		self.callbacks[id]=continuation
		self.send(node,"FIND_NODE",{
				"k" : k,
				"node" : dst,
				"id" : id,
			})
	
	def recv_found_node(self,src,pkt):
		if pkt["id"] in self.callbacks:
			self.callbacks[pkt["id"]](pkt)

	def recv_pong(self,src,pkt):
		pass

	def addNode(self,nodeid):
		d = distance(nodeid,self.me)
		# Myself, don't add that.
		if d == 0:
			return
		bucket = 1+int(math.log(d)/math.log(2))
		# Move to front
		if bucket not in self.buckets:
			self.buckets[bucket]=[]
		if nodeid in self.buckets[bucket]:
			self.buckets[bucket].remove(nodeid)
		self.buckets[bucket].insert(0,nodeid)

	def send(self,dst,t,msg):
		assert type(dst)==type(""),type(dst)
		assert dst!=""
		msg["src"]=self.me
		msg["type"]=t
		msg["dst"]=dst
		msg["networkid"]=networkid
		events.append(lambda :nodes[dst].incoming(self.me,encoder.encode(msg)))

	def incoming(self,src,msg):
		d = encoder.decode(msg)[0]
		if d["networkid"] != networkid:
			return
		self.addNode(src)
		{
			"ping"		: self.recv_ping,
			"pong" 		: self.recv_pong,
			"found_node" 	: self.recv_found_node,
			"found_value"	: self.recv_found_value,
			"find_node"	: self.recv_find_node,
			"find_value"	: self.recv_find_value,
			"store_value"	: self.recv_store,
		}[d["type"].lower()](src,d)

	def send_ping(self,dst):
		self.send(dst,"PING",{"id":1})

nodes={}

for i in range(1000):
	kademlia = Kademlia()
	nodes[kademlia.me]=kademlia

root = nodes.values()[0]

for i in nodes.values():
	i.send_ping(root.me)

def run():
	while events!=[]:
		events.pop(0)()

run()
root.iter_store_value("foo","bar",lambda :None)
run()
nodes.values()[1].iter_find_value("foo",lambda x:sys.stdout.write("Found values: "+str(x)+"\n"))
run()

x= [ (x,len(y)) for (x,y) in root.buckets.items() ]
x.sort()
print x
