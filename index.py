#!/usr/bin/python
import bisect

next_id = 0

max_size = 2

def gen_new_nodeid():
	global next_id
	next_id += 1
	return "node" + str(next_id)

def split_node(data):
	items = sorted(data)
	items1 = items[:len(items)/2]
	items2 = items[len(items)/2:]
	return (dict([ (x,data[x]) for x in items1 ]),
		dict([ (x,data[x]) for x in items2 ]))
	

def add_to_index(index,nodeid,key,value):
	assert nodeid in index,nodeid
	assert key.startswith("key")
	type,data = index[nodeid]
	if type == "data":
		data[key]=value
		if len(data) > max_size: # Needs a split
			nodeid2 = gen_new_nodeid()
			items1, items2 = split_node(data)
			if nodeid != "root":
				nodeid1 = nodeid
			else:
				nodeid1 = gen_new_nodeid()
			index[nodeid2] = ("data",items2)
			index[nodeid1] = ("data",items1)
			head1=sorted(items1)[0]
			head2=sorted(items2)[0]
			print "Splitting",nodeid,"into",nodeid1,"(",head1,")","and",nodeid2,"(",head2,")"
			assert head1.startswith("key"),head1
			assert head2.startswith("key"),head2
			if nodeid == "root":
				index[nodeid] = ("keys", { head1:nodeid1, head2:nodeid2 })
			return (
				(head1, nodeid1),
				(head2, nodeid2))
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
				lodata,hidata=split_node(data)
				lohead=sorted(lodata)[0]
				hihead=sorted(hidata)[0]
				hinodeid = gen_new_nodeid()
				if nodeid!="root":
					lonodeid = nodeid
				else:
					lonodeid = gen_new_nodeid()
					index[nodeid] = ("keys", { lohead:lonodeid, hihead:hinodeid })
				print "splitting internal node",nodeid,"into",lonodeid,hinodeid
				index[lonodeid] = ("keys",lodata)
				index[hinodeid] = ("keys",hidata)
				return ( (lohead,lonodeid), (hihead, hinodeid) )
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
		except:
			print
			pprint.pprint( db )
			raise

	#draw_dot(db)

	import math
	pprint.pprint(db)
	print len(db),"nodes"
	print len(db["root"])
	

