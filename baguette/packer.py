from intpack import *
from utils import *


def str_sanitize_strong(string):
	return str_sanitize(string, strong=True)


def str_sanitize_cc(string):
	return str_sanitize(string, cc=True)


def str_sanitize(string, cc=False, strong=False):
	out = []
	for i in string:
		i = ord(i)
		if strong:
			i &= 0x7f
		if i < 32 and (not cc or (not i in ('\r', '\n', '\t'))):
			i = 32
		out.append(i)
	return ''.join([chr(o) for o in out])


PACKER_BUFFER_SIZE = 2048


class Packer(object):
	abuffer = []
	current_index = 0
	end_index = PACKER_BUFFER_SIZE
	is_error = False

	def __init__(self):
		self.reset()

	def reset(self):
		self.is_error = False
		self.current_index = 0

	def to_buffer(v):
		self.abuffer[self.current_index] = v
		self.current_index += 1

	def to_buffer_list(alist):
		self.abuffer += self.alist
		self.current_index += len(alist)

	def add_int(self, i):
		if self.is_error:
			return

		if self.end_index - self.current_index < 6:
			self.is_error = True
		else:
			self.to_buffer_list(list(int_pack(i)))

	def add_string(self, string, limit):
		if self.is_error:
			return

		has_limit = limit > 0
		for c in string:
			if has_limit and limit == 0:
				break
			self.to_buffer(c)
			if has_limit:
				limit -= 1
			
			if self.current_index >= self.end_index:
				self.is_error = True
				break
		self.to_buffer('\x00')

	def add_raw(self, data):
		if self.is_error:
			return

		if self.current_index + len(data) >= self.end_index:
			self.is_error = True
			return
		
		self.to_buffer_list(list(data))

	def size(self):
		return len(self.abuffer)

	def data(self):
		return ''.join([chr(num) for num in self.abuffer])


SANITIZE = 1
SANITIZE_CC = 2
SKIP_START_WHITESPACES = 4


class Unpacker(object):
	start_index = 0
	current_index = 0
	end_index = PACKER_BUFFER_SIZE
	is_error = False
	data = False

	def __init__(self, data):
		self.data = data
		self.reset()

	def reset(self):
		self.is_error = False
		self.current_index = 0
		self.end_index = len(self.data)

	def get_int(self):
		
		if self.is_error:
			return

		if self.current_index >= self.end_index:
			self.is_error = True
			return

		added, anint = int_unpack(self.data[self.current_index:])
		self.current_index += added

		if self.current_index > self.end_index:
			self.is_error = True
			return

		return anint

	def get_string(self, sanitize_type=SANITIZE):
		if sanitize_type == None:
			sanitize_type = SANITIZE

		if self.is_error or self.current_index >= self.end_index:
			return ""

		astring = ""
		for c in self.data[self.current_index:]:
			self.current_index += 1
			if c == "\x00":
				break

			astring += c
		self.current_index += 1

		if sanitize_type & SANITIZE:
			astring = str_sanitize(astring)
		elif sanitize_type & SANITIZE_CC:
			astring = str_sanitize_cc(astring)
		
		return astring.lstrip(" \t\n\r") \
			if sanitize_type & SKIP_START_WHITESPACES else astring

	def get_raw(self, size):
		if self.is_error:
			return

		new_index = self.current_index + size

		if size < 0 or new_index > self.end_index:
			self.is_error = True
			return

		self.current_index = new_index
		return self.data[current_index:new_index]
