class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		try:
			self.file = open(filename, 'rb')
		except:
			raise IOError
		self.frameNum = 0
		
	def nextFrame(self, skip = 1):
		"""Get next frame."""
		for i in range(skip):
			data = self.file.read(5) # Get the framelength from the first 5 bits
			if data: 
				framelength = int(data)
								
				# Read the current frame
				data = self.file.read(framelength)
				self.frameNum += 1
		#print('Current frame number:', self.frameNum)
		print('Sent data from file', self.filename)
		return data
		
	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum
	
	