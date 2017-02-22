'''
Written by Lennart Alexander Ornberg
for SCC300 Final Year Project
'''

import Leap, os, thread, time, random, math, pickle, threading, utils, tkMessageBox
from time import sleep
from random import shuffle
from Queue import deque
from NBClassifier import NB
from Tkinter import *


class GUI:
	'''
	Main application window and program flow
	'''

	def __init__(self, master):
		'''
		Initiate window, display GUI elements and train classifiers
		'''
		self.master = master
		self.master.protocol('WM_DELETE_WINDOW', self.close)

		# Setup screen
		self.output = StringVar()
		Label(self.master, textvariable=self.output, font=('Helvetica', 16)).pack(expand=True)

		# Get controller and wait for it to initiate
		self.controller = Leap.Controller()
		sleep(0.01)

		# Load dataset
		dataset = []
		if os.path.exists('dataset.p'):
			with open('dataset.p', 'rb') as f:
				try:
					dataset = pickle.load(f)
					if not len(dataset):
						self.master.update()
						tkMessageBox.showwarning('', 'No signs in dataset.' + \
							"\nCreate signs using 'Builder.py'")
						exit()

					# Validate objects in dataset
					for sign in dataset:
						if not isinstance(sign, utils.Sign):
							self.master.update()
							tkMessageBox.showwarning('', \
								"Invalid 'dataset.p'.\n" + \
								"Use 'Builder.py' to generate a 'dataset.p'.")
							exit()
				except Exception:
					self.master.update()
					tkMessageBox.showwarning('', "Error reading 'dataset.p'")
					exit()
		else:
			self.master.update()
			tkMessageBox.showwarning('', "Missing 'dataset.p'")
			exit()

		# Sort signs from dataset by type
		fixed, gestures = [], []
		for sign in dataset:
			if len(sign.samples) >= 2:
				# If zero found across features, skip that sign
				if not utils.validateFeatures(sign.samples):
					self.master.update()
					tkMessageBox.showwarning('', \
					"Found non-zero values in sign named '" + sign.value \
					+ "', delete your samples and try re-record them with 'Builder.py'")
					exit()

				if sign.type == 'Fixed':
					for sample in sign.samples:
						# Filter out samples of invalid length
						if len(sample) == 17:
							fixed.append((sign.value, sample))
				else:
					for sample in sign.samples:
						# Filter out samples of invalid length
						if len(sample) == 200:
							gestures.append((sign.value, sample))
			else:
				self.master.update()
				tkMessageBox.showwarning('', \
					"Skipping sign named '" + sign.value + \
					"'.\nA minimum of 2 samples per class are required.")

		# Create and train classifier for fixed signs
		self.nbFixed = None
		self.nbGesture = None

		if len(fixed):
			self.nbFixed = NB()
			self.nbFixed.train(fixed)

		if len(gestures):
			self.nbGesture = NB()
			self.nbGesture.train(gestures)

		# Start thread to capture frames
		self.keepAlive = True
		thread = threading.Thread(target=self.interpret)
		thread.start()


	def classify(self, _buffer, fixed):
		'''
		Classify sign based on input and display message on result
		'''
		result = None

		# Classify fixed sign
		if fixed and self.nbFixed:
			result = self.nbFixed.probabilities(utils.vectorize(_buffer, fixed=True))

		# Classify gesture sign
		elif self.nbGesture:
			result = self.nbGesture.probabilities(utils.vectorize(_buffer, fixed=False))

		# Novelty detection based on results euclidean distance
		if result[0][2] < 0.85:
			self.output.set(result[0][0])
		else:
			self.output.set("not recognized...")
		sleep(3)
		self.output.set("")


	def close(self):
		'''
		Upon program exit, stop and wait for intepreter thread to complete
		'''
		self.keepAlive = False
		sleep(0.5)
		self.master.destroy()
		exit()


	def interpret(self):
		'''
		Main interpreter thread, detects moving or fixed signs
		'''
		moving = False

		# Captures all frames
		mainBuffer = []

		# Store frames that are part of a detected movement
		motionBuffer = []

		# Store frames that are part of a fixed gesture
		fixedBuffer = []

		# Sliding window over a 0.3 second period to smoothen detection of
		# of either gesture or fixed signs when hand is in view
		stateBuffer = deque(maxlen=30)

		# Assume that sensor is connected to begin with
		wasConnected = True

		# Main controller
		while self.keepAlive:

			# Display user notice when sensor is connected if it wasn't before
			if self.controller.is_connected:
				if not wasConnected:
					wasConnected = True
					self.master.update()
					tkMessageBox.showwarning('', 'Leap Motion sensor is connected!')

				# Capture roughly 100 frames per second
				sleep(0.01)

				# At least one hand is in view -> start capturing frames
				if len(self.controller.frame().hands) > 0:

					# Get first hand in view
					hand = self.controller.frame().hands[0]
					mainBuffer.append(hand)

					# Recorded roughly 0.1 seconds,
					# see if it is gesture or fixed
					if len(mainBuffer) > 10:

						# Check last 0.01 second if moving or not
						if utils.moving(mainBuffer[-10], mainBuffer[-1]):
							stateBuffer.append(1)
						else:
							stateBuffer.append(0)

						# Still moving -> keep filling moving buffer
						if sum(stateBuffer) > 15:
							if not moving:
								moving = True
								fixedBuffer = []
							motionBuffer.append(hand)

						else:
							# Movement stopped -> analyze
							if len(motionBuffer) > 30:
								self.classify(motionBuffer, False)
								moving = False
								mainBuffer = []
								motionBuffer = []
								fixedBuffer = []

							# Fixed sign held for 0.4 seconds -> analyze
							elif len(fixedBuffer) > 40:
								self.classify(fixedBuffer, True)
								mainBuffer = []
								motionBuffer = []
								fixedBuffer = []

							# Hand is still -> keep filling fixed buffer
							else:
								fixedBuffer.append(hand)

				# Hand is out of view -> analyze if we have more than 30 frames
				else:
					if len(motionBuffer) > 30:
						self.classify(motionBuffer, False)
						sleep(0.01)
					mainBuffer = []
					motionBuffer = []

			else:
				# Display user notice if sensor was disconnect and
				# was connected before
				if wasConnected:
					wasConnected = False
					self.master.update()
					tkMessageBox.showwarning('', 'Leap Motion sensor is disconnected')


def main():
	'''
	Initiate GUI loop
	'''
	root = Tk()
	root.resizable(width=FALSE, height=FALSE)
	root.geometry('{}x{}'.format(300, 150))
	root.wm_title("Interpreter")

	app = GUI(root)
	root.mainloop()

# Run application
main()
