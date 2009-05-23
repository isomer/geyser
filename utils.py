import UserList
import bisect

class SortedList(UserList.UserList):
	def __init__(self, comparison=cmp, initlist = None):
		self.comparison = comparison
		UserList.UserList.__init__(self, initlist)
		self.data.sort()

	def __setslice__(self, i, j, other):
		UserList.UserList.__setstate__(i,j,other)
		self.data.sort()

	def __cmp__(self, other):
		raise Exception("Not Implemented")

	def __setitem__(self, i, item):
		UserList.UserList.__setitem__(self, i, item)
		self.data.sort()

	def append(self, item):
		bisect.insort_left(self.data, item)

	def insert(self, i, item):
		self.append(item)

	def reverse(self):
		raise Exception("Can't reverse a sorted list!")

	def sort(self):
		pass

	def extend(self, other):
		UserList.UserList.extend(self, other)
		self.data.sort()

if __name__ == "__main__":
	a=SortedList()
	a.append(2)
	a.append(3)
	a.append(1)
	print a
