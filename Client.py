from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	
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
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0

	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def createWidgets(self):
		"""Build GUI."""
		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		
		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 
	
	def setupMovie(self):
		"""Setup button handler."""
		if self.state == self.INIT:
			self.sendRtspRequest(self.SETUP)
			self.openRtpPort()
	
	def exitClient(self):
		"""Teardown button handler."""
		if self.state == self.READY or self.state == self.READY:
			self.sendRtspRequest(self.TEARDOWN)
			self.rtspSocket.close()
			self.rtpSocket.close()
			self.master.destroy()

	def pauseMovie(self):
		"""Pause button handler."""
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)
	
	def playMovie(self):
		"""Play button handler."""
		if self.state == self.READY:
			self.sendRtspRequest(self.PLAY)
	
	def listenRtp(self):		
		"""Listen for RTP packets."""
		#TODO
					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		#TODO
	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		#TODO
		
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
		except:
			tkinter.messagebox.showwarning('Failed to connect to server with IP address', self.serverAddr, 'and port', self.serverPort)
		threading.Thread(target = self.recvRtspReply).start()
	
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		command = ['SETUP', 'PLAY', 'PAUSE', 'TEARDOWN']

		self.rtspSeq += 1
		request = command[requestCode] + ' ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\n'
		if requestCode == self.SETUP:
			request += 'Transport: RTP/UDP; client_port= ' + str(self.rtpPort)
		print(request)

		self.requestSent = requestCode

		#print('Sending ' + command[requestCode] + ' request.....')
		self.rtspSocket.sendall(request.encode('utf-8'))
		#print('Request sent')
	
	
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		while True:
			try:
				data = self.rtspSocket.recv(256)
			except:
				break
			if data:
				print("Data received:\n" + data.decode("utf-8"))
				self.parseRtspReply(data.decode("utf-8"))
	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		reply = data.split('\n')
		seq = int(reply[1].split(' ')[1])
		session = int(reply[2].split(' ')[1])

		if seq != self.rtspSeq:
			return
		
		if self.state == self.INIT:
			self.sessionId = session
		
		if self.sessionId != session:
			return

		if self.requestSent == self.SETUP:
			self.state = self.READY
		elif self.requestSent == self.PLAY:
			self.state = self.PLAYING
		elif self.requestSent == self.PAUSE:
			self.state = self.READY
		elif self.requestSent == self.TEARDOWN:
			self.state = self.INIT
		
	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		# self.rtpSocket = ...
		
		# Set the timeout value of the socket to 0.5sec
		# ...
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.rtpSocket.settimeout(0.5)
		try:
			self.rtpSocket.connect((self.serverAddr, self.serverPort))
		except:
			tkinter.messagebox.showwarning('Failed to connect to server with IP address', self.serverAddr, 'and port', self.serverPort)
		

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		self.exitClient()
