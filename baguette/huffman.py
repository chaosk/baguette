
HUFFMAN_EOF_SYMBOL = 256
HUFFMAN_MAX_SYMBOLS=HUFFMAN_EOF_SYMBOL+1
HUFFMAN_MAX_NODES=HUFFMAN_MAX_SYMBOLS*2-1
HUFFMAN_LUTBITS = 10
HUFFMAN_LUTSIZE = (1<<HUFFMAN_LUTBITS)
HUFFMAN_LUTMASK = (HUFFMAN_LUTSIZE-1)

_freq_table = [
	1<<30,4545,2657,431,1950,919,444,482,2244,617,838,542,715,1814,304,240,754,212,647,186,
	283,131,146,166,543,164,167,136,179,859,363,113,157,154,204,108,137,180,202,176,
	872,404,168,134,151,111,113,109,120,126,129,100,41,20,16,22,18,18,17,19,
	16,37,13,21,362,166,99,78,95,88,81,70,83,284,91,187,77,68,52,68,
	59,66,61,638,71,157,50,46,69,43,11,24,13,19,10,12,12,20,14,9,
	20,20,10,10,15,15,12,12,7,19,15,14,13,18,35,19,17,14,8,5,
	15,17,9,15,14,18,8,10,2173,134,157,68,188,60,170,60,194,62,175,71,
	148,67,167,78,211,67,156,69,1674,90,174,53,147,89,181,51,174,63,163,80,
	167,94,128,122,223,153,218,77,200,110,190,73,174,69,145,66,277,143,141,60,
	136,53,180,57,142,57,158,61,166,112,152,92,26,22,21,28,20,26,30,21,
	32,27,20,17,23,21,30,22,22,21,27,25,17,27,23,18,39,26,15,21,
	12,18,18,27,20,18,15,19,11,17,33,12,18,15,19,18,16,26,17,18,
	9,10,25,22,22,17,20,16,6,16,15,20,14,18,24,335,1517]

class Huffman(object):

	class Node(object):
		def __init__(self):
			self.bits = 0
			self.num_bits = 0
			self.leafs = 2*[0]
			self.symbol = 0

	class ConstructNode(object):
		def __init__(self):
			self.node_id = 0
			self.frequency = 0

	def __init__(self):
		self.nodes = [Huffman.Node() for i in xrange(HUFFMAN_MAX_NODES)]
		self.decode_lut = HUFFMAN_LUTSIZE*[None]
		self.num_nodes = 0
		self.start_node = None
		self._construct_tree(_freq_table)

		for i in xrange(HUFFMAN_LUTSIZE):
			bits = i
			node = self.start_node
			j = 0
			while j < HUFFMAN_LUTBITS:
				node = self.nodes[node.leafs[bits&1]]
				bits >>= 1
				if node.num_bits:
					self.decode_lut[i] = node
					break
				j += 1
			if j == HUFFMAN_LUTBITS:
				self.decode_lut[i] = node

	def set_bits_r(self, node, bits, depth):
		if node.leafs[1] != 0xffff:
			self.set_bits_r(self.nodes[node.leafs[1]], bits|(1<<depth), depth+1)
		if node.leafs[0] != 0xffff:
			self.set_bits_r(self.nodes[node.leafs[0]], bits, depth+1)

		if node.num_bits:
			node.bits = bits
			node.num_bits = depth

	@staticmethod
	def _bubble_sort(alist, size):
		changed = 1
		while changed:
			changed = 0
			for i in xrange(size-1):
				if alist[i].frequency < alist[i+1].frequency:
					temp = alist[i]
					alist[i] = alist[i+1]
					alist[i+1] = temp
					changed = 1
			size -= 1

	def _construct_tree(self, freq_table):
		nodes_left_storage = [Huffman.ConstructNode() for i in xrange(HUFFMAN_MAX_SYMBOLS)]
		nodes_left = [Huffman.ConstructNode() for i in xrange(HUFFMAN_MAX_SYMBOLS)]
		num_nodes_left = HUFFMAN_MAX_SYMBOLS

		for i in xrange(HUFFMAN_MAX_SYMBOLS):
			self.nodes[i].num_bits = 0xFFFFFFFF
			self.nodes[i].symbol = i
			self.nodes[i].leafs[0] = 0xffff
			self.nodes[i].leafs[1] = 0xffff

			if i == HUFFMAN_EOF_SYMBOL:
				nodes_left_storage[i].frequency = 1
			else:
				nodes_left_storage[i].frequency = freq_table[i]
			nodes_left_storage[i].node_id = i
			nodes_left[i] = nodes_left_storage[i]

		self.num_nodes = HUFFMAN_MAX_SYMBOLS
		while num_nodes_left > 1:
			Huffman._bubble_sort(nodes_left, num_nodes_left)

			self.nodes[self.num_nodes].num_bits = 0
			self.nodes[self.num_nodes].leafs[0] = nodes_left[num_nodes_left-1].node_id
			self.nodes[self.num_nodes].leafs[1] = nodes_left[num_nodes_left-2].node_id
			nodes_left[num_nodes_left-2].node_id = self.num_nodes
			nodes_left[num_nodes_left-2].frequency = nodes_left[num_nodes_left-1].frequency + nodes_left[num_nodes_left-2].frequency

			self.num_nodes += 1
			num_nodes_left -= 1

		self.start_node = self.nodes[self.num_nodes-1]
		self.set_bits_r(self.start_node, 0, 0)

	def _load_symbol(self, symbol, bits, bit_count):
		bits |= self.nodes[symbol].bits << bit_count
		bit_count += self.nodes[symbol].num_bits
		return (bits, bit_count)

	def _write(self, bits, bit_count, dst):
		while bit_count >= 8:
			dst.append(bits&0xff)
			bits >>= 8
			bit_count -= 8
		return (bits, bit_count)

	def compress(self, input):
		# This does NOT work!
		# 
		# It returns strange values when first character is 'w'
		# and the second character is not 'w'.

		raise NotImplementedError

		num = 0
		bits = 0
		bit_count = 0
		input_size = len(input)
		output = []
		if input_size:
			symbol = ord(input[num])
			num += 1
			while num != input_size:
				bits, bit_count = self._load_symbol(symbol, bits, bit_count)
				symbol = ord(input[num])
				bits, bit_count = self._write(bits, bit_count, output)
				num += 1

		bits, bit_count = self._load_symbol(symbol, bits, bit_count)
		bits, bit_count = self._write(bits, bit_count, output)

		output.append(bits&0xff)
		return ''.join([chr(num_) for num_ in output])

	def decompress(self, input):
		num = 0
		input_size = len(input)
		bits = 0
		bit_count = 0
		eof = id(self.nodes[HUFFMAN_EOF_SYMBOL])
		node_id = None
		output = []
		while 1:
			node = None
			if bit_count >= HUFFMAN_LUTBITS:
				node_num = bits&HUFFMAN_LUTMASK
				node = self.decode_lut[node_num]
				node_id = id(self.decode_lut[node_num])

			while bit_count < 24 and num != input_size:
				bits |= ord(input[num])<<bit_count
				bit_count += 8
				num += 1

			if node is None:
				node_num = bits&HUFFMAN_LUTMASK
				node = self.decode_lut[node_num]
				node_id = id(self.decode_lut[node_num])

			if node is None:
				return ValueError

			if node.num_bits:
				bits >>= node.num_bits
				bit_count -= node.num_bits
			else:
				bits >>= HUFFMAN_LUTBITS
				bit_count -= HUFFMAN_LUTBITS
				while 1:
					node_num = node.leafs[bits&1]
					node = self.nodes[node_num]
					node_id = id(self.nodes[node_num])
					bit_count -= 1
					bits >>= 1
					if node.num_bits:
						break
					if bit_count == 0:
						return None

			if eof == node_id or bit_count <= 0:
				break

			output.append(node.symbol)
		return ''.join([chr(num_) for num_ in output])
