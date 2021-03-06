from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os, time

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	DESCRIBE = 4
	BACKWARD = 5
	FORWARD = 6
	SWITCH = 7
	
	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.describeRequest = False
		self.teardownAcked = 0
		self.startRecvRtspReply = threading.Event()
		self.getFrame = threading.Event()
		self.waitCommand = threading.Event()
		self.waitCommand.set()
		self.caculationEvent = threading.Event()
		self.caculationEvent.set()
		self.connectToServer()
		self.frameNbr = 0
		self.frameLoss = 0
		self.sumData = 0
		self.sumOfTime = 0
		self.frameSkipped = 0
		self.setupMovie()

	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def createWidgets(self):
		"""Build GUI."""
		# Create Setup button
		#self.setup = Button(self.master, width=20, padx=3, pady=3)
		#self.setup["text"] = "Setup"
		#self.setup["command"] = self.setupMovie
		#self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=2, column=0, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=2, column=1, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Stop"
		self.teardown["command"] =  self.stopMovie
		self.teardown.grid(row=2, column=2, padx=2, pady=2)

		# Create Describe button
		self.describe = Button(self.master, width=20, padx=3, pady=3)
		self.describe["text"] = "Describe"
		self.describe["command"] = self.describeMovie
		self.describe.grid(row=2, column=3, padx=3, pady=3)

		# Create Backward button
		self.backward = Button(self.master, width=20, padx=3, pady=3)
		self.backward["text"] = "<<"
		self.backward["command"] = self.backwardMovie
		self.backward.grid(row=1, column=1, padx=3, pady=3)

		# Create Forward button
		self.forward = Button(self.master, width=20, padx=3, pady=3)
		self.forward["text"] = ">>"
		self.forward["command"] = self.forwardMovie
		self.forward.grid(row=1, column=2, padx=3, pady=3)

		# Create Switch video button
		self.switch = Button(self.master, width=20, padx=3, pady=3)
		self.switch["text"] = "Switch video"
		self.switch["command"] = self.switchMovie
		self.switch.grid(row=1, column=4, padx=3, pady=3)
		
		# Create a label to display the movie
		self.label = Label(self.master, height = 19)
		self.label.grid(row = 0, column = 0, columnspan= 4, padx= 5, pady= 5)

        # Menu listbox
		self.listMenu = Listbox(self.master, height=19, width=20, bg='#EBECF0', highlightcolor='#D3D3D3', selectmode=SINGLE)
		self.listMenu.grid(row=0, column=4, padx=5, pady=5)

		# Display time
		self.currTime = StringVar()
		self.currTime.set("00:00")
		self.currTimeLabel = Label(self.master, textvariable=self.currTime)
		self.currTimeLabel.grid(row=1, column=0, padx=3, pady=3)
	
	def setupMovie(self):
		"""Setup button handler -> run without button"""
		if self.state == self.INIT:
			print('Setting up movie.....\n')
			self.startRecvRtspReply.set()
			self.sendRtspRequest(self.SETUP)
			self.openRtpPort()
			print('Set up done\n')
	
	def exitClient(self):
		"""Stop button handler."""
		if self.state == self.READY or self.state == self.PLAYING:
			self.pauseMovie()
			self.waitCommand.wait()
			self.waitCommand.clear()
			self.teardownAcked = 1
			self.sendRtspRequest(self.TEARDOWN)
			self.rtspSocket.close()
			self.rtpSocket.close()
			self.master.destroy()
			os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)

			print('Data rate:', float(self.sumData / self.sumOfTime / 1024), 'KB/s')
			print('Loss rate: ' + str(float(self.frameLoss / (self.frameNbr + self.frameSkipped)) * 100) + '%')
	
	def stopMovie(self):
		"""Stop button handler"""
		self.pauseMovie()
		self.waitCommand.wait()
		self.waitCommand.clear()
		#self.fileName = str(self.listMenu.get(ACTIVE))
		self.frameNbr = 0
		self.sendRtspRequest(self.SWITCH)

	def switchMovie(self):
		"""Switch button handler"""
		self.pauseMovie()
		self.waitCommand.wait()
		self.waitCommand.clear()
		self.fileName = str(self.listMenu.get(ACTIVE))
		self.frameNbr = 0
		self.sendRtspRequest(self.SWITCH)

	def pauseMovie(self):
		"""Pause button handler."""
		if self.state == self.PLAYING:
			#print(self.waitCommand.is_set())
			self.waitCommand.wait()
			self.waitCommand.clear()
			self.getFrame.set()
			self.sendRtspRequest(self.PAUSE)
	
	def playMovie(self):
		"""Play button handler."""
		if self.state == self.READY:
			self.waitCommand.wait()
			self.waitCommand.clear()
			self.getFrame.clear()
			self.sendRtspRequest(self.PLAY)
	
	def describeMovie(self):
		"""Describe button handler."""
		self.pauseMovie()
		self.waitCommand.wait()
		self.waitCommand.clear()
		self.sendRtspRequest(self.DESCRIBE)
		#self.playMovie()

	def backwardMovie(self):
		"""Backward button handler."""
		#self.pauseMovie()
		#self.playMovie()
		if self.state == self.PLAYING:
			self.waitCommand.wait()
			self.waitCommand.clear()
			self.sendRtspRequest(self.BACKWARD)

			self.caculationEvent.wait()
			self.caculationEvent.clear()
			self.frameNbr -= 99
			self.frameSkipped += 99
			if self.frameNbr < 0:
				self.frameNbr = 0
			self.caculationEvent.set()

	def forwardMovie(self):
		"""Forward button handler."""
		#self.pauseMovie()
		#self.playMovie()
		if self.state == self.PLAYING:
			self.waitCommand.wait()
			self.waitCommand.clear()
			self.sendRtspRequest(self.FORWARD)

			self.caculationEvent.wait()
			self.caculationEvent.clear()
			self.frameNbr += 99
			self.frameSkipped -= 99
			self.caculationEvent.set()
	
	def listenRtp(self):
		"""Listen for RTP packets."""
		#print('Listening RTP')
		clock = time.time()
		while True:
			#print(self.frameNbr)
			if self.getFrame.is_set():
				break
			try:
				data = self.rtpSocket.recv(20480)
				self.sumData += len(data)
			except socket.error as error:
				if not self.getFrame.is_set() and self.teardownAcked == 0:
					tkinter.messagebox.showerror('ERROR', error)
					print('socket.error -', error)
					break
			if data:
				rtpPacket = RtpPacket()
				rtpPacket.decode(data)
				#print('RTP packet size:', bytearray(data).__sizeof__())
				currFrameNbr = rtpPacket.seqNum()

				if currFrameNbr > self.frameNbr:
					self.caculationEvent.wait()
					self.caculationEvent.clear()
					self.frameLoss += currFrameNbr - self.frameNbr - 1
					self.frameNbr = currFrameNbr
					self.caculationEvent.set()

					self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
					self.updateTime()
			else:
				break
		self.sumOfTime += time.time() - clock
		print('Stopped listening to RTP packets\n')
	
	def updateTime(self):
		sec = int(self.frameNbr / 20)
		mm = int(sec / 60)
		ss = sec % 60
		self.currTime.set("{:02d}:{:02d}".format(mm, ss))
					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		tempFileName = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
		file = open(tempFileName, 'wb')
		file.write(data)
		file.close()
		return tempFileName
	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		frame = ImageTk.PhotoImage(Image.open(imageFile))
		self.label.configure(image= frame, height= 300) 
		self.label.image = frame

		
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		#self.rtspSocket.settimeout(5)
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
		except:
			tkinter.messagebox.showwarning('CONNECTION ERROR', 'Failed to connect to server with IP address ' + str(self.serverAddr) + ' and port ' + str(self.serverPort) + '. Please choose another IP address or port')
		threading.Thread(target = self.recvRtspReply).start()
	
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""
		command = ['SETUP', 'PLAY', 'PAUSE', 'TEARDOWN', 'DESCRIBE', 'BACKWARD', 'FORWARD', 'SWITCH']

		self.rtspSeq += 1
		request = command[requestCode] + ' ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq)
		if requestCode == self.SETUP:
			request += '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)

		self.rtspSocket.sendall(request.encode('utf-8'))
		print('Data sent:\n' + request + '\n')

		if requestCode != self.DESCRIBE:
			self.requestSent = requestCode
		else:
			self.describeRequest = True
	
	
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		self.startRecvRtspReply.wait()
		#print('Crossed the line')
		while True:
			#print('Listening to RTSP reply.....\n')
			try:
				data = self.rtspSocket.recv(256)
			except:
				break
			print('Received data\n')
			if data:
				print("Data received:\n" + data.decode("utf-8") + '\n')
				self.parseRtspReply(data.decode("utf-8"))
			self.waitCommand.set()
			#print('Processed RTSP reply.....\n')
		print('Stopped receiving RTSP reply\n')

	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""

		reply = data.split('\n')
		seq = int(reply[1].split(' ')[1])
		session = int(reply[2].split(' ')[1])

		if reply[0] != 'RTSP/1.0 200 OK':
			print('An error has occured in the server')
			return

		if seq != self.rtspSeq:
			return
		
		if self.state == self.INIT:
			self.sessionId = session
		
		if self.sessionId != session:
			return

		if self.describeRequest:
			description = ''
			for line in reply[3:]:
				description += line + '\n'
			tkinter.messagebox.showinfo('Video Description', description)
			self.describeRequest = False
		elif self.requestSent == self.SETUP and self.state == self.INIT:
			self.state = self.READY
			print('Current state set to READY\n')
			fileList = reply[3:]
			ind = 0
			for file in fileList:
				self.listMenu.insert(ind,file)
				ind += 1
		elif self.requestSent == self.PLAY and self.state == self.READY:
			self.state = self.PLAYING
			print('Current state set to PLAYING\n')
			threading.Thread(target = self.listenRtp).start()
		elif self.requestSent == self.PAUSE and self.state == self.PLAYING:
			self.state = self.READY
			print('Current state set to PAUSE\n')
		elif self.requestSent == self.TEARDOWN and (self.state == self.READY or self.state == self.PLAYING):
			self.state = self.INIT
			print('Current state set to INIT\n')
		elif self.requestSent == self.BACKWARD:
			print('Video just moved backward\n')
		elif self.requestSent == self.FORWARD:
			print('Video just moved forward\n')
		elif self.requestSent == self.SWITCH:
			print('Successfully switched video\n')
	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.rtpSocket.settimeout(0.5)
		try:
			self.rtpSocket.bind((self.serverAddr, self.rtpPort))
		except:
			tkinter.messagebox.showwarning('CONNECTION ERROR', 'Failed to connect to server with IP address ' + str(self.serverAddr) + ' and port ' + str(self.serverPort) + ', because you are using an unavailable RTP port')


	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		self.pauseMovie()
		if tkinter.messagebox.askokcancel("WARNING!!!", "Are you sure you want to stop watching your video and exit?"):
			if self.state == self.INIT:
				self.rtspSocket.close()
				self.master.destroy()
				self.startRecvRtspReply.set()
			else:
				self.exitClient()
		else:
			self.playMovie()
