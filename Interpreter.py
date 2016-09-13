'''
Written by Lennart Alexander Ornberg
for SCC300 Final Year Project
'''

import Leap, sys, thread, time, random, math, pickle, threading, utils
from time import sleep
from random import shuffle
from Queue import deque
from NBClassifier import NB
from Tkinter import *


# Main application window
# --------------------------------------------------
class GUI:
	def __init__(self, master):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.close)

		#Setup screen
		self.output = StringVar()
		Label(self.master, textvariable=self.output, font=("Helvetica", 16)).pack(expand=True)

		self.controller = Leap.Controller()
		sleep(0.01) #wait for leap controller to initiate
		dataset = pickle.load(open("dataset.p","rb")) #load dataset of signs

		if len(dataset) == 0:
			print "No signs in dataset"
			exit()

		fixed, gestures = [], []

		#Sort signs from dataset by type
		for sign in dataset:
			if sign.type == 'Fixed':
				for sample in sign.samples:
					fixed.append((sign.value, sample))
			else:
				for sample in sign.samples:
					gestures.append((sign.value, sample))

		#Create and train classifier for fixed signs
		self.nbFixed = NB()
		self.nbFixed.train(fixed)

		#Create and train classifier for gesture signs
		self.nbGesture = NB()
		self.nbGesture.train(gestures)

		self.keepAlive = True
		thread = threading.Thread(target=self.interpret)
		thread.start()

	#Main classifier function
	def classify(self, _buffer, fixed):
		result = None

		if fixed: #Classify fixed sign
			result = self.nbFixed.probabilities(utils.vectorize(_buffer, 1))
		
		else: #Classify gesture sign
			result = self.nbGesture.probabilities(utils.vectorize(_buffer, 10))
		
		if result[0][2] < 0.85: #Novelty detection based on results euclidean distance
			self.output.set(result[0][0])
		else:
			self.output.set("not recognized...")		
		sleep(3)
		self.output.set("")

	#Upon program exit, interpreter thread
	def close(self):
		self.keepAlive = False
		sleep(0.5)
		self.master.destroy()

	#Main interpreter thread, listening for movement or fixed signs
	def interpret(self):
		moving = False
		mainBuffer = [] #minimum frames to be filled before filling of motion or fixed buffer can occur
		motionBuffer = []
		fixedBuffer = []
		stateBuffer = deque(maxlen=30) #sliding window

		#Main controller
		while self.keepAlive:
			if self.controller.is_connected:
				sleep(0.01)
				if len(self.controller.frame().hands) > 0:
					hand = self.controller.frame().hands[0]
					mainBuffer.append(hand)
					if len(mainBuffer) > 10:

						#Check last 0.01 second if moving or not
						if utils.moving(mainBuffer[-10], mainBuffer[-1]):
							stateBuffer.append(1)
						else:
							stateBuffer.append(0)

						#Still moving -> keep filling moving buffer
						if sum(stateBuffer) > 15:
							#print "moving"
							if not moving:
								moving = True
								fixedBuffer = []
							motionBuffer.append(hand)

						else:
							#Movement stopped -> analyze 
							if len(motionBuffer) > 30:
								self.classify(motionBuffer, False)
								moving = False
								mainBuffer = []
								motionBuffer = []
								fixedBuffer = []

							#Fixed sign held for 0.4 seconds -> analyze
							elif len(fixedBuffer) > 40:
								self.classify(fixedBuffer, True)
								mainBuffer = []
								motionBuffer = []
								fixedBuffer = []

							#Hand is still -> keep filling fixed buffer
							else:
								fixedBuffer.append(hand)
					
				#Hand is out of view -> analyze we have more than 30 frames
				else:
					if len(motionBuffer) > 30:
						self.classify(motionBuffer, False)
						sleep(0.01)
					mainBuffer = []
					motionBuffer = []



# Initiate main application window
# --------------------------------------------------
root = Tk()
root.resizable(width=FALSE, height=FALSE)
root.geometry('{}x{}'.format(300, 150))
root.wm_title("Interpreter")

app = GUI(root)
root.mainloop()
