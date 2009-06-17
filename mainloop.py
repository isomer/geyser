import select
import time
import heapq

readers=[]
writers=[]
timers=[]

running = True

def addReader(reader):
	readers.append(reader)

def delReader(reader):
	readers.remove(reader)

def addWriter(writer):
	writers.append(writer)

def delWriter(writer):
	writers.remove(writer)

def run():
	while running:
		now = time.time()
		while timers!=[] and timers[0][0] <= now:
			(expire, cb) = heapq.heappop(timers)
		if timers!=[]:
			expire = timers[0][0]-time.time()
		else:
			expire = None
		try:
			(r,w,x) = select.select(readers, writers, [], expire)
		except TypeError:
			print readers,writers,expire
			raise
		for i in r:
			i.readEvent()
		for i in w:
			i.writeEvent()

