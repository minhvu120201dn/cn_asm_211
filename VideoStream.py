class VideoStream:
	frameLocation = {}

	def __init__(self, filename):
		self.filename = filename
		try:
			self.file = open(filename, "rb")
		except:
			raise IOError
		self.frameNum = 0
		self.currLocation = 0
		if not filename in self.frameLocation:
			self.frameLocation[filename] = [0]

	def nextFrame(self, skip=1):
		"""Get next frame."""
		for i in range(skip):
			data = self.file.read(5)  # Get the framelength from the first 5 bytes
			if data:
				framelength = int(data)

				# Read the current frame
				data = self.file.read(framelength)

				# Update class attributes
				if self.currLocation > self.frameLocation[self.filename][-1]:
					self.frameLocation[self.filename].append(self.currLocation)
				self.frameNum += 1
				self.currLocation += 5 + framelength

		# print('Current frame number:', self.frameNum)
		# print('Sent data from file', self.filename)
		return data

	def prevFrame(self, skip=1):
		"""Get previous frame."""
		self.frameNum -= skip
		if self.frameNum < 0:
			self.frameNum = 0

		self.currLocation = self.frameLocation[self.filename][self.frameNum]

		self.file.seek(self.currLocation)

	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum
