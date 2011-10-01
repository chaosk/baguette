#!/usr/bin/env python
# encoding: utf-8
"""
baguette.py
"""

import os
import sys
import argparse
import struct
import logging
from struct import pack, unpack
logger = logging.getLogger('baguette')
debug_handler = logging.StreamHandler()
debug_handler.setLevel(logging.DEBUG)
debug_formatter = logging.Formatter('%(asctime)s :: %(name)s :: %(levelname)s :: %(message)s')
debug_handler.setFormatter(debug_formatter)
output_handler = logging.StreamHandler()
output_handler.setLevel(logging.INFO)
output_formatter = logging.Formatter('%(message)s')
output_handler.setFormatter(output_formatter)

from commentary import Commentator
from constants import *
from delta import Delta, Snapshot
from huffman import Huffman
from intpack import int_decompress
from network import get_net_class_for, get_net_message_for
from packer import Unpacker
from utils import int_to_chars, chars_to_int

from progressbar import ProgressBar, AnimatedMarker, Bar
from progressbar import ETA, FormatLabel, Percentage


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
		logger.info("Header was read.")
		logger.info("Size of this demo is {0} bytes."
			" It's {2:02}:{3:02} long (~{1} ticks).".format(
				os.stat(f.name).st_size, self.length * 50,
				*divmod(self.length, 60)))


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
		self.last_snapshot = None
		self.key_frames = []


class Demo(object):

	def __init__(self, demo_file=None, already_loaded=False, cli=False):
		self.cli = cli
		if not already_loaded:
			try:
				self.demo_file = open(demo_file, 'rb')
			except IOError, e:
				raise e
		else:
			self.demo_file = demo_file

	def analyze(self):
		self.header = Header(self.demo_file)
		self.huffman = Huffman()
		self.delta = Delta()
		self.info = DemoInfo()
		self.rounds = []
		self.commentator = Commentator(self)

		# skip the commercials (map)
		self.demo_file.seek(HEADER_SIZE + self.header.map_size)

		self.find_keyframes()
		logger.debug("Finished finding keyframes")


		if self.cli:
			maxval = self.info.last_tick - self.info.first_tick
			pbar = ProgressBar(
				widgets=["Processing demo...", Percentage(), Bar(), ETA()],
				maxval=maxval).start()
			while True:
				try:
					self.do_tick()
				except DemoFileEnded:
					break
				pbar.update(self.info.current_tick - self.info.first_tick)
			pbar.finish()
		else:
			while True:
				try:
					self.do_tick()
				except DemoFileEnded:
					break
		logger.info("Finished analyzing demo")

	def find_keyframes(self):
		start_position = self.demo_file.tell()

		while True:
			current_position = self.demo_file.tell()

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
				if chunk_tick > 2:
					# dirty.
					self.info.last_tick = chunk_tick
			elif chunk_size:
				self.demo_file.read(chunk_size)

		self.demo_file.seek(start_position)

	def read_chunk_header(self, tick=0):
		size = 0

		try:
			chunk = unpack('B', self.demo_file.read(1))[0]
		except struct.error:
			raise DemoFileEnded

		if chunk & CHUNKTYPEFLAG_TICKMARKER:
			tick_delta = chunk & CHUNKMASK_TICK
			atype = chunk & (CHUNKTYPEFLAG_TICKMARKER | CHUNKTICKFLAG_KEYFRAME)

			if not tick_delta:
				try:
					tick_data = unpack('4c', self.demo_file.read(4))
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
					size = unpack('B', self.demo_file.read(1))[0]
				except struct.error:
					raise DemoFileEnded
			elif size == 0x1f:
				try:
					size_data = unpack('2B', self.demo_file.read(2))
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

			if chunk_size and chunk_tick:
				self.info.current_tick = chunk_tick
				self.current_tick = chunk_tick

			if chunk_size:
				compressed = self.demo_file.read(chunk_size)
				if len(compressed) != chunk_size:
					raise DemoFileEnded("Error reading chunk")

				decompressed = self.huffman.decompress(compressed)

				if not len(decompressed):
					raise InvalidDemo("Error during network decompression")

				data = int_decompress(decompressed)

				if not len(data):
					raise InvalidDemo("Error during intpack decompression")

			if chunk_type == CHUNKTYPE_DELTA:
				# <del>There was no need to implement it.</del>
				# <ins>There was need to implement it.</ins>
				snapshot = self.delta.unpack(data)
				self.do_snapshot(snapshot)
			elif chunk_type == CHUNKTYPE_SNAPSHOT:
				data_pointer = 2
				data_size, item_count = data[:data_pointer]
				offsets = data[data_pointer:data_pointer+item_count]
				data_pointer = data_pointer + item_count

				snapshot = Snapshot()

				for i in xrange(item_count):
					try:
						item_size = offsets[i+1] - offsets[i]
					except IndexError:
						# the last item
						item_size = data_size - offsets[i]
					item_size = item_size / 4
					item = data[data_pointer:data_pointer+item_size]
					data_pointer = data_pointer + item_size

					type_and_id, item_data = item[0], item[1:]
					atype = type_and_id >> 16
					id = type_and_id & 0xffff

					snapshot.new_item(type_and_id, item_data)

				self.do_snapshot(snapshot)

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

	def do_snapshot(self, snapshot):
		for key, item in snapshot.items.iteritems():
			netobj = get_net_class_for(item.type())()
			netobj.assign_fields(item.data)

			if not netobj.ignorable:
				netobj.process(self.commentator)

		self.delta.set_snapshot(snapshot)

	def do_message(self, msg_id, unpacker):
		message = get_net_message_for(msg_id)()
		message.unpacker = unpacker
		message.collect_data()

		if not message.ignorable:
			message.process(self.commentator)



def main(argv=None):
	parser = argparse.ArgumentParser(description='Baguette. Teeworlds demo reader.')
	parser.add_argument('-v', '--version', action='version',
		version='%(prog)s 0.2')
	parser.add_argument('demofile', type=argparse.FileType('rb'),
		help='path to teeworlds demo')
	parser.add_argument('-d', '--debug', action='store_true', help="DON'T.")

	args = parser.parse_args()
	if args.debug:
		logger.setLevel(logging.DEBUG)
		logger.addHandler(debug_handler)
		logger.debug("Entered debug mode!")
	else:
		logger.setLevel(logging.INFO)
		logger.addHandler(output_handler)
	logger.info("Baguette!\nTeeworlds demo parser\n")
	logger.info("Opened file \"{0}\"".format(args.demofile.name))
	demo = Demo(args.demofile, already_loaded=True, cli=True)
	demo.analyze()

if __name__ == "__main__":
	sys.exit(main())
