#!/usr/bin/env python
import utils

class ReliableSender:
	def __init__(self,pktGenerator):
		self.cwnd = 1
		self.ssthresh = None
		self.ooo = 0  # out of order packets
		self.pktGenerator = pktGenerator
		self.rto = 300
		self.setTimeout(1,self.tick)
		self.seq = 0
		self.outstanding = {}
		self.trySend()

	def trySend(self):
		while len(self.outstanding) < self.cwnd and self.pktGenerator is not None:
			try:
				print self.getTime(),"Sending",self.cwnd,len(self.outstanding),self.ssthresh
				self.seq+=1
				self.send((self.seq,self.pktGenerator.next()))
				self.outstanding[self.seq]=self.getTime()
			except StopIteration:
				print "End of input"
				self.pktGenerator=None
		print "outstanding=",sorted(self.outstanding.keys()),len(self.outstanding)

	def send(self,msg):
		pass

	def setTimeout(self,ts,cb):
		pass

	def getTime(self):
		pass

	def tick(self):
		print self.getTime(),"tick"
		for k,v in self.outstanding.items():
			if self.getTime() - v > self.rto:
				self.gotLoss()
				self.outstanding={}
				break
		if self.pktGenerator is not None:
			self.setTimeout(10,self.tick)

	def gotAck(self,ack):
		print self.getTime(),"ack",ack,"cwnd=",self.cwnd,"ssthresh=",self.ssthresh
		self.lastts=self.getTime()
		if self.outstanding!={}:
			expected = sorted(self.outstanding.keys())[0]
			if expected == ack:
				# Update rate control
				if self.ssthresh is None or self.cwnd < self.ssthresh:
					self.cwnd += 1
				else:
					self.cwnd += 1.0/self.cwnd
				self.ooo=0
			elif ack>expected:
				self.ooo+=1
				if self.ooo >= 3:
					#del self.outstanding[expected]
					self.gotLoss()
					self.outstanding={}
					self.ooo = 0
			else:
				# Older than expected ack
				pass
					
				
		if ack in self.outstanding:
			del self.outstanding[ack]
		self.trySend()

	def recv(self,msg):
		self.gotAck(msg[1])

	def gotLoss(self):
		print self.getTime(),"LOSS"
		self.ssthresh = self.cwnd / 2
		self.cwnd = 1
		self.lastts=self.getTime()
		self.trySend()

class ReliableReceiver:
	def __init__(self,consumer):
		self.consumer = consumer

	def recv(self, pkt):
		self.consumer(pkt)

	def send(self, pkt):
		pass
		
class MGroupSimulator:
	def __init__(self):
		self.queue = []
		self.timers = utils.SortedList()
		self.listeners = []
		self.ts=0
		self.leader=None

	def addGroup(self,listener):
		self.listeners.append(listener)
		listener.group = self

	def send(self,pkt):
		self.queue = (self.queue + [pkt])[:10]

	def sendToLeader(self,pkt):
		self.leader.recv(pkt)

	def getTime(self):
		return self.ts

	def addTimer(self,timeout,cb):
		self.timers.append((timeout+self.ts,cb))

	def run(self):
		while self.queue or self.timers:
			if self.queue:
				pkt=self.queue.pop(0)
				for i in self.listeners:
					i.recv(pkt)
			self.ts+=1
			while self.timers!=[] and self.timers[0][0]<=self.ts:
				ts,cb = self.timers.pop(0)
				cb()

class ReliableSenderSimulator(ReliableSender):
	def __init__(self,group,*args):
		self.group = group
		self.group.leader = self
		print "got hereish"
		ReliableSender.__init__(self,*args)
		
	def send(self,msg):
		self.group.addTimer(1,lambda :self.group.send(msg))

	def setTimeout(self,duration,cb):
		self.group.addTimer(duration,cb)

	def getTime(self):
		return self.group.getTime()

class ReliableReceiverSimulator(ReliableReceiver):
	def recv(self,msg):
		self.group.sendToLeader(("ack",msg[0]))

if __name__=="__main__":
	import sys
	g=MGroupSimulator()
	x=ReliableSenderSimulator(g,iter(xrange(1000000)))
	y=ReliableReceiverSimulator(lambda x:sys.stdout.write("R:"+str(x)+"\n"))
	g.addGroup(y)

	g.run()
	
