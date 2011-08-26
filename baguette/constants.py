
DEMO_VERSION = 3
HEADER_SIZE = 176

CHUNK_SIZE = 1
TICK_DATA_SIZE = 4

CHUNKTYPEFLAG_TICKMARKER = 0x80
CHUNKTICKFLAG_KEYFRAME = 0x40
CHUNKMASK_TICK = 0x3f
CHUNKMASK_TYPE = 0x60
CHUNKMASK_SIZE = 0x1f
CHUNKTYPE_SNAPSHOT = 1
CHUNKTYPE_MESSAGE = 2
CHUNKTYPE_DELTA = 3
CHUNKFLAG_BIGSIZE = 0x10