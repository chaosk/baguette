
def int_unpack(input):
	added = 1
	sign = ord(input[0])>>6&1
	out = ord(input[0])&0x3f
	if not (ord(input[0]) & 0x80):
		out ^= -sign
		return added, out
	out |= (ord(input[1])&0x7f)<<6
	added += 1
	
	if not (ord(input[1]) & 0x80):
		out ^= -sign
		return added, out
	out |= (ord(input[2])&0x7f)<<13
	added += 1
	
	if not (ord(input[2]) & 0x80):
		out ^= -sign
		return added, out
	out |= (ord(input[3])&0x7f)<<20
	added += 1
	
	if not (ord(input[3]) & 0x80):
		out ^= -sign
		return added, out
	out |= (ord(input[4])&0x7f)<<27
	out ^= -sign
	added += 1
	return added, out


def int_pack(input):
	added = 1
	out = []
	out.append((input>>25)&0x40)
	input = input^(input>>31)
	out[0] |= input&0x3f
	input >>= 6
	if input:
		out[0] |= 0x80
		while True:
			out.append(input&(0x7f))
			input >>= 7
			out[added] |= (input!=0)<<7
			added += 1
			if input == 0:
				break
	return ''.join([chr(num) for num in out])


def int_decompress(input):
	num = 0
	size = len(input)
	out = []
	while num < size:
		num_, out_ = int_unpack(input[num:])
		num += num_
		out.append(out_)
	return out


def int_compress(input):
	return ''.join([int_pack(num) for num in input])
