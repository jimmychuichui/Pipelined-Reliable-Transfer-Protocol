# packet.py
import struct
import zlib
# Packet format: | seq_num (I) | ack_num (I) | flags (B) | window_size (H) | length (H) | data (variable) |
# I - unsigned int (4 bytes)
# B - unsigned char (1 byte)
# H - unsigned short (2 bytes)

PACKET_HEADER_FORMAT = '!IIBHH'
PACKET_HEADER_SIZE = struct.calcsize(PACKET_HEADER_FORMAT)

# Flags
SYN = 0x1
ACK = 0x2
FIN = 0x4


def create_packet(seq_num, ack_num, flags, window_size, data=b''):
    # create a checksum with the data and the header
    length = len(data)
    header = struct.pack(PACKET_HEADER_FORMAT, seq_num, ack_num, flags, window_size, length)
    return header + data

def parse_packet(packet_bytes):
    header = packet_bytes[:PACKET_HEADER_SIZE]
    seq_num, ack_num, flags, window_size, length = struct.unpack(PACKET_HEADER_FORMAT, header)
    data = packet_bytes[PACKET_HEADER_SIZE:PACKET_HEADER_SIZE + length]
    
    return seq_num, ack_num, flags, window_size, data
