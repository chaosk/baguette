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


AWSUM_LUT = [
	"\x80", "\x81", "\x82", "\x83", "\x84", "\x85", "\x86", "\x87",
	"\x88", "\x89", "\x8a", "\x8b", "\x8c", "\x8d", "\x8e", "\x8f",
	"\x90", "\x91", "\x92", "\x93", "\x94", "\x95", "\x96", "\x97",
	"\x98", "\x99", "\x9a", "\x9b", "\x9c", "\x9d", "\x9e", "\x9f",
	"\xa0", "\xa1", "\xa2", "\xa3", "\xa4", "\xa5", "\xa6", "\xa7",
	"\xa8", "\xa9", "\xaa", "\xab", "\xac", "\xad", "\xae", "\xaf",
	"\xb0", "\xb1", "\xb2", "\xb3", "\xb4", "\xb5", "\xb6", "\xb7",
	"\xb8", "\xb9", "\xba", "\xbb", "\xbc", "\xbd", "\xbe", "\xbf",
	"\xc0", "\xc1", "\xc2", "\xc3", "\xc4", "\xc5", "\xc6", "\xc7",
	"\xc8", "\xc9", "\xca", "\xcb", "\xcc", "\xcd", "\xce", "\xcf",
	"\xd0", "\xd1", "\xd2", "\xd3", "\xd4", "\xd5", "\xd6", "\xd7",
	"\xd8", "\xd9", "\xda", "\xdb", "\xdc", "\xdd", "\xde", "\xdf",
	"\xe0", "\xe1", "\xe2", "\xe3", "\xe4", "\xe5", "\xe6", "\xe7",
	"\xe8", "\xe9", "\xea", "\xeb", "\xec", "\xed", "\xee", "\xef",
	"\xf0", "\xf1", "\xf2", "\xf3", "\xf4", "\xf5", "\xf6", "\xf7",
	"\xf8", "\xf9", "\xfa", "\xfb", "\xfc", "\xfd", "\xfe", "\xff",
	"\x00", "\x01", "\x02", "\x03", "\x04", "\x05", "\x06", "\x07",
	"\x08", "\t",   "\n",   "\x0b", "\x0c", "\r",   "\x0e", "\x0f",
	"\x10", "\x11", "\x12", "\x13", "\x14", "\x15", "\x16", "\x17",
	"\x18", "\x19", "\x1a", "\x1b", "\x1c", "\x1d", "\x1e", "\x1f",
	" ",    "!",    "\"",   "#",    "$",    "%",    "&",    "'",
	"(",    ")",    "*",    "+",    ",",    "-",    ".",    "/",
	"0",    "1",    "2",    "3",    "4",    "5",    "6",    "7",
	"8",    "9",    ":",    ";",    "<",    "=",    ">",    "?",
	"@",    "A",    "B",    "C",    "D",    "E",    "F",    "G",
	"H",    "I",    "J",    "K",    "L",    "M",    "N",    "O",
	"P",    "Q",    "R",    "S",    "T",    "U",    "V",    "W",
	"X",    "Y",    "Z",    "[",    "\\",   "]",    "^",    "_",
	"`",    "a",    "b",    "c",    "d",    "e",    "f",    "g",
	"h",    "i",    "j",    "k",    "l",    "m",    "n",    "o",
	"p",    "q",    "r",    "s",    "t",    "u",    "v",    "w",
	"x",    "y",    "z",    "{",    "|",    "}",    "~",    "\x7f",
]


def ints_to_string(num):
	return ''.join([''.join([
		AWSUM_LUT[(val>>24)&0xff],
		AWSUM_LUT[(val>>16)&0xff],
		AWSUM_LUT[(val>>8)&0xff],
		AWSUM_LUT[val&0xff]
	]) for val in num]).partition('\x00')[0]


def int_to_chars(num):
	return [(num>>24)&0xff, (num>>16)&0xff, (num>>8)&0xff, num&0xff]


def chars_to_int(alist):
	if len(alist) != 4:
		raise ValueError
	else:
		return (alist[0]<<24) | (alist[1]<<16) | (alist[2]<<8) | alist[3]
