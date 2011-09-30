#!/usr/bin/env python
# -*- coding: utf-8 -*-

from struct import unpack

"""
This file is part of tml.

Licensed under GNU General Public License

Sources:
- https://github.com/erdbeere/tml/blob/master/tml/utils.py
- SushiTee himself.
"""

def int32(x):
	if x>0xFFFFFFFF:
		print x
		raise OverflowError
	if x>0x7FFFFFFF:
		x=int(0x100000000-x)
		if x<2147483648:
			return -x
		else:
			return -2147483648
	return x


def safe_chr(i):
	return chr(max(0, min(i if i >= 0 else 256 + i, 256)))


def ints_to_string(num):
	return ''.join([''.join([
		chr(max(0, min(((val>>24)&0xff)-128 if ((val>>24)&0xff) >= 128 else 256 + ((val>>24)&0xff)-128, 255))),
		chr(max(0, min(((val>>16)&0xff)-128 if ((val>>16)&0xff) >= 128 else 256 + ((val>>16)&0xff)-128, 255))),
		chr(max(0, min(((val>>8)&0xff)-128 if ((val>>8)&0xff) >= 128 else 256 + ((val>>8)&0xff)-128, 255))),
		chr(max(0, min((val&0xff)-128 if val&0xff >= 128 else 256 + (val&0xff)-128, 255))),
		]) for val in num]).partition('\x00')[0]


def int_to_chars(num):
	return [(num>>24)&0xff, (num>>16)&0xff, (num>>8)&0xff, num&0xff]


def chars_to_int(alist):
	if len(alist) != 4:
		raise ValueError
	else:
		return (alist[0]<<24) | (alist[1]<<16) | (alist[2]<<8) | alist[3]
