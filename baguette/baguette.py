#!/usr/bin/env python
# encoding: utf-8
"""
baguette.py
"""

import sys
import argparse

from reader import DemoReader

class Demo(object):

	def __init__(self, demo_file=None, already_loaded=False):
		if not already_loaded:
			try:
				self.demo_file = open(demo_file, 'rb')
			except IOError, e:
				raise e
		else:
			self.demo_file = demo_file
		self.reader = DemoReader(self.demo_file)


def main(argv=None):
	parser = argparse.ArgumentParser(description='Baguette. Teeworlds demo reader.')
	parser.add_argument('-v', '--version', action='version',
		version='%(prog)s 0.1')
	parser.add_argument('demofile', type=argparse.FileType('rb'),
		help='path to teeworlds demo')
	parser.add_argument('-d', '--debug', action='store_true', help="DON'T.")

	args = parser.parse_args()
	demo = Demo(args.demofile, already_loaded=True)
	if args.debug:
		f=demo.demo_file
		# import pdb
		# pdb.set_trace()


if __name__ == "__main__":
	sys.exit(main())
