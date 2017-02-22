'''
Written by Lennart Alexander Ornberg
for SCC300 Final Year Project
'''

import Leap, sys, os, thread, time, random, math, threading, pickle, tkMessageBox, utils
from time import sleep
from Tkinter import *


class SetNameDialog:
	'''
	Dialog for creation of new sign
	'''
	def __init__(self, parent):
		top = self.top = Toplevel(parent)
		top.wm_title("New Sign")

		# Display entry for sign name/value
		Label(top, text='Word:').grid(row=0, pady=5)
		self.myEntryBox = Entry(top)
		self.myEntryBox.grid(row=0, column=1, columnspan=3)

		# Display selection of sign type
		Label(top, text='Type:').grid(row=1, column=0, pady=5)
		self.radioButtonValue = IntVar()
		Radiobutton(top, text="Gesture", variable=self.radioButtonValue, value=0).grid(row=1, column=1, pady=5)
		Radiobutton(top, text="Fixed", variable=self.radioButtonValue, value=1).grid(row=1, column=2)

		# Display OK button to return to main screen
		Button(top, text='OK', command=self.send).grid(row=3, column=1, columnspan=2, pady=2)
		self.value = ''


	def send(self):
		'''
		Upon closing of window, store values collected
		'''
		if self.radioButtonValue.get() == 0:
			self.signType = 'Gesture'
		else:
			self.signType = 'Fixed'

		self.value = self.myEntryBox.get()
		self.top.destroy()


class GUI:
	'''
	Main application window and program flow
	'''
	def __init__(self, master):
		'''
		Initiate window, set variables and display GUI elements
		'''

		# Get controllers and set variables
		self.master = master
		self.master.protocol('WM_DELETE_WINDOW', self.close)
		self.dataset = []
		self.vectorBuffer = []

		# Get exising dataset if exists, or start with a blank one
		if os.path.exists('dataset.p'):
			with open('dataset.p', 'rb') as f:
				try:
					self.dataset = pickle.load(f)
					# Validate objects in dataset
					for sign in self.dataset:
						if not isinstance(sign, utils.Sign):
							self.master.update()
							tkMessageBox.showwarning('', \
								"Found non-sign object in 'dataset.p'\n" + \
								' Creating a new empty dataset.')
							self.master.update()
							self.dataset = []
							break
				except Exception:
					self.master.update()
					tkMessageBox.showwarning('', 'Error reading file.\n' + \
						'Creating a new empty dataset.')
					self.dataset = []

		# Get controller and wait for it to initiate
		self.controller = Leap.Controller()
		sleep(0.01)

		# List and scrollbar for Signs
		self.signsScrollbar = Scrollbar(master)
		self.signsList = Listbox(master, yscrollcommand=self.signsScrollbar.set, exportselection=0)
		self.signsList.grid(row=0, rowspan=5, column=0, columnspan=2)
		self.signsList.bind('<<ListboxSelect>>', self.signsListBoxSelect)
		self.signsScrollbar.config(command=self.signsList.yview)
		self.signsScrollbar.grid(row=0, column=2, rowspan=5, sticky=N+S)

		# List and scrollbar for samples
		self.samplesScrollbar = Scrollbar(master)
		self.samplesList = Listbox(master, yscrollcommand=self.samplesScrollbar.set)
		self.samplesList.grid(row=0, rowspan=5, column=3, columnspan=2)
		self.samplesScrollbar.config(command=self.samplesList.yview)
		self.samplesScrollbar.grid(row=0, column=5, rowspan=5, sticky=N+S)

		# Buttons for controlling signs
		self.deleteSign = Button(master, text="Delete", command=self.deleteSign)
		self.deleteSign.grid(row=6, column=0)
		self.createSignButton = Button(master, text="New", command=self.createSign)
		self.createSignButton.grid(row=6, column=1)

		# Buttons for controlling samples
		self.deleteSampleButton = Button(master, text="Delete Last", command=self.deleteSample)
		self.deleteSampleButton.grid(row=6, column=3)
		self.recordButton = Button(master, text="Record")
		self.recordButton.bind("<Button-1>", self.startRecording)
		self.recordButton.bind("<ButtonRelease-1>", self.stopRecording)
		self.recordButton.grid(row=6, column=4)

		# Boolean for use by recorder thread
		self.isRecording = False

		# Initate first list
		self.updateSignsList()

		# No current selected sign
		self.currentSign = None


	def updateSignsList(self):
		'''
		Update signs list by clearing out current list
		and inserting in new entries one from dataset in alphabetical order
		'''
		self.signsList.delete(0, END)
		self.dataset = sorted(self.dataset, key=lambda x : x.value)
		for sign in self.dataset: #List in alphabetical order
			self.signsList.insert(END, ' '+sign.value)


	def updateSamplesList(self):
		'''
		Update samples list by deleting all list entries
		and re-insert all from dataset
		'''
		# Update list to current selected sign
		if self.currentSign != None:
			self.samplesList.delete(0, END)
			for i in range(len(self.currentSign.samples)):
				self.samplesList.insert(END, ' '+str(i+1))
			self.samplesList.yview(END)
		# Empty list
		else:
			self.samplesList.delete(0, END)


	def startRecording(self, event):
		'''
		Start recording of frames in separate thread
		if controller is connected and a hand is in view
		'''
		self.vectorBuffer = []
		if self.controller.is_connected:
			if len(self.controller.frame().hands) != 0:
				if self.currentSign != None:
					# Start recording
					self.isRecording = True
					thread = threading.Thread(target=self._record)
					thread.start()
				else:
					tkMessageBox.showwarning('','No sign selected')
			else:
				tkMessageBox.showwarning('','No hand in view')
		else:
			tkMessageBox.showwarning('','Leap Motion sensor not connected')


	def _record(self):
		'''
		Record roughly 100 frames per second, store in 'vectorBuffer'
		'''
		while self.isRecording:
			if len(self.controller.frame().hands) != 0:
				hand = self.controller.frame().hands[0]
				self.vectorBuffer.append(hand)
				sleep(0.01)
			else:
				self.isRecording = False
				tkMessageBox.showwarning('','No hand in view')


	def stopRecording(self, event):
		'''
		Stop ongoing recording of frames, and based on sign type
		(fixed or gesture) convert buffer of frames to a vector with
		the corresponding length
		'''
		if self.isRecording:
			value = self.currentSign
			 # Kill recording thread
			self.isRecording = False

			# If sign recorded was fixed/static and has at least one frame
			if self.currentSign.type == 'Fixed' and len(self.vectorBuffer):
				self.currentSign.samples.append(utils.vectorize(self.vectorBuffer, fixed=True))

			# Make sure we have enough frames to create 10 keyframes for
			# gestures signs
			elif len(self.vectorBuffer) >= 10:
				self.currentSign.samples.append((self.vectorBuffer, fixed=False))

			# Not enough frames were recorded, return before making changes
			else:
				tkMessageBox.showwarning('', 'Too few frames recorded. Try again')
				return

			# Check that features across all samples are non-zero
			if len(self.currentSign.samples) >= 2:
				if not utils.validateFeatures(self.currentSign.samples):
					tkMessageBox.showwarning('', \
						'Zero-values recorded from sensor. Delete samples for current sign and try again')

			# Just to be safe, update dataset file despite not exiting program
			pickle.dump(self.dataset, open('dataset.p', 'wb'))
			self.updateSamplesList()


	def createSign(self):
		'''
		Create new sign object, prompt for sign type
		and update sign list
		'''
		# Open dialog to set sign name
		inputDialog = SetNameDialog(self.master)
		self.master.wait_window(inputDialog.top)

		# Assure sign has name and is unique
		value = inputDialog.value
		if len(value) > 0 and sum([1 for x in self.dataset if x.value == value]) == 0:
			# Create new Sign object
			self.currentSign = utils.Sign(value, inputDialog.signType, [])
			self.dataset.append(self.currentSign)

		# Update GUI accordigly
		self.updateSignsList()


	def deleteSign(self):
		'''
		Prompt for confirmation and deleted sign if affirmative
		'''
		selected = self.signsList.curselection()

		# Any sign selected?
		if len(selected) > 0:
			if tkMessageBox.askyesno("Delete", "Are you sure you want to delete this sign?"):
				self.currentSign = None
				del self.dataset[selected[0]]
				self.updateSignsList()
				self.updateSamplesList()
		else:
			tkMessageBox.showwarning('','No sign selected')


	def deleteSample(self):
		'''
		Delete last sample of selected sign
		'''
		selected = len(self.currentSign.samples) - 1
		if selected >= 0:
			del self.currentSign.samples[selected]
			self.updateSamplesList()
		else:
			tkMessageBox.showwarning('','No samples to delete')


	def signsListBoxSelect(self, event):
		'''
		On user select of sign, set variable reference
		and trigger update of GUI list
		'''
		selected = event.widget.curselection()

		# Set current sign to the corresponding selected list items
		if len(selected) > 0:
			# Make sure 'selected' is int; cover for older tkinter versions
			self.currentSign = self.dataset[int(selected[0])]
		self.updateSamplesList()


	def close(self):
		'''
		Save dataset before exiting
		'''
		pickle.dump(self.dataset, open('dataset.p', 'wb'))
		self.master.destroy()


def main():
	'''
	Main program function; initate GUI
	'''
	# Start main Tkinter loop
	root = Tk()
	root.resizable(width=FALSE, height=FALSE)
	root.wm_title("Builder")
	app = GUI(root)
	root.mainloop()


# Run application
main()
