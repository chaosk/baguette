try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO

from struct import pack, unpack
import struct

from commentary import Commentary
from constants import *
from huffman import Huffman
from intpack import int_decompress
from network import *
from packer import *
from utils import int_to_chars, chars_to_int


class InvalidDemo(Exception):
	pass


class DemoFileEnded(Exception):
	pass


class Header(object):

	def __init__(self, f):
		sig = ''.join(unpack('7c', f.read(7)))
		if sig != 'TWDEMO\x00':
			raise InvalidDemo('Invalid signature')
		self.version, = unpack('c', f.read(1))
		if ord(self.version) != DEMO_VERSION:
			raise InvalidDemo('Wrong version')
		try:
			header = unpack('64s64s4s4s8s4s20s', f.read(168))
		except struct.error, e:
			raise InvalidDemo('Invalid demo header')
		self.net_version, self.map_name, self.map_size, \
		self.map_crc, self.type, self.length, \
		self.timestamp = [chars_to_int([ord(m) for m in tuple(s)]) \
			if len(s) == 4 else s.strip('\x00') \
			if isinstance(s, str) else s for s in header]


class KeyFrame(object):
	def __init__(self, file_position, tick):
		self.file_position = file_position
		self.tick = tick


class DemoInfo(object):
	def __init__(self):
		self.seekable_points = 0
		self.first_tick = None
		self.current_tick = None
		self.last_tick = None
		self.key_frames = []


class DemoReader(object):

	def __init__(self, demo_file):
		self.f = demo_file
		self.header = Header(self.f)
		self.huffman = Huffman()

		self.info = DemoInfo()

		self.commentary = Commentary()

		# skip the commercials (map)
		self.f.seek(HEADER_SIZE + self.header.map_size)

		self.find_keyframes()

		while True:
			try:
				self.do_tick()
			except DemoFileEnded:
				break

		# add game commentary
		# self.process_game()
		# import pdb
		# pdb.set_trace()
		

	def find_keyframes(self):
		start_position = self.f.tell()

		while True:
			current_position = self.f.tell()
			
			try:
				chunk_type, chunk_size, chunk_tick = self.read_chunk_header()
			except DemoFileEnded:
				break

			if chunk_type & CHUNKTYPEFLAG_TICKMARKER:
				if chunk_type & CHUNKTICKFLAG_KEYFRAME:
					key_frame = KeyFrame(
						file_position=current_position,
						tick=chunk_tick
					)
					self.info.key_frames.append(key_frame)
					self.info.seekable_points += 1

				if self.info.first_tick == None:
					self.info.first_tick = chunk_tick
				self.info.last_tick = chunk_tick
			elif chunk_size:
				self.f.read(chunk_size)

		self.f.seek(start_position)

	def read_chunk_header(self, tick=0):
		size = 0

		try:
			chunk = unpack('B', self.f.read(1))[0]
		except struct.error:
			raise DemoFileEnded

		if chunk & CHUNKTYPEFLAG_TICKMARKER:
			tick_delta = chunk & CHUNKMASK_TICK
			atype = chunk & (CHUNKTYPEFLAG_TICKMARKER | CHUNKTICKFLAG_KEYFRAME)

			if not tick_delta:
				try:
					tick_data = unpack('4c', self.f.read(4))
				except struct.error:
					raise DemoFileEnded
				tick = chars_to_int([ord(t) for t in tick_data])
			else:
				if tick == None:
					tick = 0
				tick += tick_delta
		else:
			atype = (chunk & CHUNKMASK_TYPE) >> 5
			size = chunk & CHUNKMASK_SIZE

			if size == 0x1e:
				try:
					size = unpack('B', self.f.read(1))[0]
				except struct.error:
					raise DemoFileEnded
			elif size == 0x1f:
				try:
					size_data = unpack('2B', self.f.read(2))
				except struct.error:
					raise DemoFileEnded
				size = (size_data[1]<<8) | size_data[0]
		return (atype, size, tick)

	def do_tick(self):
		chunk_tick = self.info.current_tick

		while True:
			try:
				chunk_type, chunk_size, chunk_tick = self.read_chunk_header(chunk_tick)
			except DemoFileEnded:
				raise

			if chunk_size:
				compressed = self.f.read(chunk_size)
				if len(compressed) != chunk_size:
					raise DemoFileEnded("Error reading chunk")

				decompressed = self.huffman.decompress(compressed)
				
				if not len(decompressed):
					raise InvalidDemo("Error during network decompression")

				data = int_decompress(decompressed)

				if not len(data):
					raise InvalidDemo("Error during intpack decompression")

			if chunk_type == CHUNKTYPE_DELTA:
				# NotImplemented
				# 
				# There was no need to implement it.
				pass
			elif chunk_type == CHUNKTYPE_SNAPSHOT:
				data_pointer = 2
				data_size, item_count = data[:data_pointer]
				offsets = data[data_pointer:data_pointer+item_count]
				data_pointer = data_pointer + item_count
				
				for i in xrange(item_count):
					try:
						item_size = offsets[i+1] - offsets[i]
					except IndexError:
						# the last item
						item_size = data_size - offsets[i]
					item_size = item_size / 4
					item = data[data_pointer:data_pointer+item_size]
					data_pointer = data_pointer + item_size

					type_and_id = item[0]
					atype = type_and_id >> 16
					id = type_and_id & 0xffff

					netobj = get_net_class_for(atype)()
					netobj.assign_fields(item[1:])

					if not netobj.ignorable:
						netobj.process(self.commentary)

			elif chunk_type == CHUNKTYPEFLAG_TICKMARKER:
				break
			elif chunk_type == CHUNKTYPE_MESSAGE:
				data = pack('{0}i'.format(len(data)), *data)
				unpacker = Unpacker(data)
				msg_id = unpacker.get_int()
				sys = msg_id & 1
				msg_id >>= 1

				if not sys:
					self.do_message(msg_id, unpacker)

	def do_message(self, msg_id, unpacker):
		message = get_net_message_for(msg_id)()
		message.unpacker = unpacker
		message.collect_data()

		if not message.ignorable:
			message.process(self.commentary)
