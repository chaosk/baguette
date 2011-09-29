from collections import OrderedDict
from network import get_net_class_for

class DemoError(Exception):
	pass

class Delta(object):

	def __init__(self):
		self.previous_snapshot = None

	def set_snapshot(self, snapshot):
		self.previous_snapshot = snapshot

	def unpack(self, data):
		deleted_count, updated_count, temp_count = data[:3]
		data = data[3:]

		snapshot_to = Snapshot() # init builder

		deleted, data = data[:deleted_count], data[deleted_count:]

		snapshot_from = self.previous_snapshot
		
		if snapshot_from:
			for key, item in snapshot_from.items.iteritems():
				if not key in deleted:
					snapshot_to.new_item(key, item.data) # i guess

		# updated shit
		for i in range(updated_count):
			if len(data) <= 2:
				raise DemoError # in tw return -1
			atype, id, data = data[0], data[1], data[2:] # slow :/
			net_obj = get_net_class_for(atype)()
			item_size = len(net_obj.get_attr_proto())

			if net_obj.ignorable:
				data = data[item_size:]
				continue

			# range check
			if len(data) - item_size < 0 or item_size < 0:
				raise DemoError # in tw return -3

			key = (atype<<16)|id

			from_data = snapshot_to.get_item_data(key) # should return None if... well because of the next line
			new_data, data = data[:item_size], data[item_size:]
			if from_data:
				new_data = self.undiff_item(from_data, new_data)

			new_item = snapshot_to.get_item(key) # we need a builder :P
			if not new_item:
				snapshot_to.new_item(key, new_data)
			else:
				new_item.data = new_data

		return snapshot_to # or what ever xD

	def undiff_item(self, from_data, diff_data): # item_size needed?
		# data should be ints
		out_data = []
		for i in xrange(len(diff_data)):
			out_data.append(from_data[i]+diff_data[i])
			# if _diff == 0:
			# 	# self.snapshot_data_rate[self.current_snapshot] += 1
			# else:
			# 	# _str = int_pack(_diff)
			# 	# self.snapshot_data_rate[self.current_snapshot] += len(_str) * 8
		return out_data


class SnapshotItem(object):

	def __init__(self, type_and_id):
		self.type_and_id = type_and_id
		self.data = None

	def type(self):
		return self.type_and_id>>16

	def id(self):
		return self.type_and_id&0xffff

	def key(self):
		return self.type_and_id


class Snapshot(object):

	def __init__(self):
		self.data_size = 0
		self.num_items = 0
		self.items = OrderedDict() # SnapshotItems
		#self.offsets = [] # needed in python?

	def get_item(self, key):
		try:
			return self.items[key]
		except KeyError:
			return None

	def get_item_data(self, key):
		try:
			return self.items[key].data
		except KeyError:
			return None

	def new_item(self, key, data):
		item = SnapshotItem(key)
		item.data = data
		self.items[key] = item
		self.num_items += 1
		return item
