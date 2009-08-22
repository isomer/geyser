#!/usr/bin/python
import bisect

next_id = 0

max_size = 10

def gen_new_nodeid():
	global next_id
	next_id += 1
	return "node" + str(next_id)

def split_data(data):
	items = sorted(data)
	items1 = items[:len(items)/2]
	items2 = items[len(items)/2:]
	return (dict([ (x,data[x]) for x in items1 ]),
		dict([ (x,data[x]) for x in items2 ]))
	
def split_node(index,nodeid,(type,data)):
	assert nodeid.startswith("node") or nodeid=="root",nodeid
	lodata,hidata=split_data(data)
	lohead=sorted(lodata)[0]
	hihead=sorted(hidata)[0]
	hinodeid = gen_new_nodeid()
	if nodeid!="root":
		lonodeid = nodeid
	else:
		lonodeid = gen_new_nodeid()
		index[nodeid] = ("keys", { lohead:lonodeid, hihead:hinodeid })
	print "splitting node",nodeid,"into",lonodeid,hinodeid
	index[lonodeid] = (type,lodata)
	index[hinodeid] = (type,hidata)
	return ( (lohead,lonodeid), (hihead, hinodeid) )

def add_to_index(index,nodeid,key,value):
	assert nodeid in index,nodeid
	assert key.startswith("key")
	type,data = index[nodeid]
	if type == "data":
		data[key]=value
		if len(data) > max_size: # Needs a split
			return split_node(index,nodeid,(type,data))
		else:
			index[nodeid] = ("data",data)
			assert sorted(data)[0].startswith("key")
			return ((sorted(data)[0],nodeid),)
	else:
		items = sorted(data)
		location = bisect.bisect_right(items, key)
		#print key,"in",items,"->",items[location]
		location = max(location-1,0)
		assert items[location] <= key or location==0, (location, key, items[location])
		#assert items[location] > key, (key,items[location-1])
		ret=add_to_index(index, data[items[location]], key, value)
		if len(ret) == 1:
			((lokey1,lonodeid1),) = ret
			assert lokey1.startswith("key"),lokey1
			if data[items[location]] != lonodeid1:
				print "updating one key",lokey1,":",data[items[location]],"->",lonodeid1
			del data[items[location]]
			data[lokey1]=lonodeid1
			index[nodeid] = ("keys", data)
			return ((sorted(data)[0],nodeid),)
		else:
			#print "updating",len(ret),"keys"
			del data[items[location]]
			for (lokey,lonodeid) in ret:
				data[lokey]=lonodeid
			if len(data) > max_size:
				return split_node(index,nodeid,(type,data))
			else:
				index[nodeid] = ("keys", data)
				return ((sorted(data)[0],nodeid),)

if __name__ == "__main__":
	import pprint
	import random


	def draw_dot(db):
		print "digraph g {"
		for i in db:
			if db[i][0]=="keys":
				for j,k in db[i][1].items():
					print i,"->",k,"[label=\"%s\"];" % j
		print "}"
	db = { "root" : ("data",{}) }
	blocks = range(30)
	random.shuffle(blocks)
	for i in blocks:
		try:
			add_to_index(db,"root","key%d" % i,"value%d" % i)
			print
			pprint.pprint(db)
		except:
			print
			pprint.pprint( db )
			raise

	#draw_dot(db)

	import math
	pprint.pprint(db)
	print len(db),"nodes"
	print len(db["root"])
	

