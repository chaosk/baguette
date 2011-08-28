#!/usr/bin/env python
# encoding: utf-8
"""
baguette.py
"""

import sys
import argparse
import logging
logger = logging.getLogger('baguette')
debug_handler = logging.StreamHandler()
debug_handler.setLevel(logging.DEBUG)
debug_formatter = logging.Formatter('%(asctime)s :: %(name)s :: %(levelname)s :: %(message)s')
debug_handler.setFormatter(debug_formatter)
output_handler = logging.StreamHandler()
output_handler.setLevel(logging.INFO)
output_formatter = logging.Formatter('%(message)s')
output_handler.setFormatter(output_formatter)

# logger.addHandler(debug_handler)

from reader import DemoReader

class Demo(object):

	def __init__(self, demo_file=None, already_loaded=False, cli=False):
		if not already_loaded:
			try:
				self.demo_file = open(demo_file, 'rb')
			except IOError, e:
				raise e
		else:
			self.demo_file = demo_file
		self.reader = DemoReader(self.demo_file, cli)


def main(argv=None):
	parser = argparse.ArgumentParser(description='Baguette. Teeworlds demo reader.')
	parser.add_argument('-v', '--version', action='version',
		version='%(prog)s 0.1')
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

if __name__ == "__main__":
	sys.exit(main())
