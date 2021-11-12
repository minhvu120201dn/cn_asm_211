import sys
from time import time
HEADER_SIZE = 12

class RtpPacket:	
	header = bytearray(HEADER_SIZE)
	
	def __init__(self):
		pass
		
	def encode(self, version, padding, extension, cc, seqnum, marker, pt, ssrc, payload):
		"""Encode the RTP packet with header fields and payload."""
		timestamp = int(time())
		#--------------
		# TO COMPLETE
		#--------------
		
		# Get the payload from the argument
		# self.payload = ...
		self.header[0] = (version << 6) | (padding << 5) | (extension << 4) | cc
		self.header[1] = (marker << 7) | pt
		self.header[2] = seqnum >> 8
		self.header[3] = seqnum
		self.header[4] = timestamp >> 24
		self.header[5] = (timestamp >> 16) & 0xff
		self.header[6] = (timestamp >> 8) & 0xff
		self.header[7] = timestamp & 0xff
		self.header[8] = ssrc >> 24
		self.header[9] = (ssrc >> 16) & 0xff
		self.header[10] = (ssrc >> 8) & 0xff
		self.header[11] = ssrc & 0xff
		self.payload = payload
		#print('Payload size:', bytearray(self.payload).__sizeof__())
		
	def decode(self, byteStream):
		"""Decode the RTP packet."""
		self.header = bytearray(byteStream[:HEADER_SIZE])
		self.payload = byteStream[HEADER_SIZE:]
		#print('Payload size:', bytearray(self.payload).__sizeof__())
	
	def version(self):
		"""Return RTP version."""
		return int(self.header[0] >> 6)
	
	def seqNum(self):
		"""Return sequence (frame) number."""
		seqNum = self.header[2] << 8 | self.header[3]
		return int(seqNum)
	
	def timestamp(self):
		"""Return timestamp."""
		timestamp = self.header[4] << 24 | self.header[5] << 16 | self.header[6] << 8 | self.header[7]
		return int(timestamp)
	
	def payloadType(self):
		"""Return payload type."""
		pt = self.header[1] & 127
		return int(pt)
	
	def getPayload(self):
		"""Return payload."""
		return self.payload
		
	def getPacket(self):
		"""Return RTP packet."""
		return self.header + self.payload