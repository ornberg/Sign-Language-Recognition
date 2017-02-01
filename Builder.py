'''
Written by Lennart Alexander Ornberg
for SCC300 Final Year Project
'''

import Leap, sys, os, thread, time, random, math, threading, pickle, tkMessageBox, utils
from time import sleep
from Tkinter import *

Sign = utils.Sign #import common Sign class
dataset = [] #global dataset for writing to file



# Dialog for creation of a new sign
# --------------------------------------------------
class SetNameDialog:
	def __init__(self, parent):
		top = self.top = Toplevel(parent)
		top.wm_title("New Sign")

		#For entry of word value
		Label(top, text='Word:').grid(row=0, pady=5)
		self.myEntryBox = Entry(top)
		self.myEntryBox.grid(row=0, column=1, columnspan=3)

		#For selection of sign type
		Label(top, text='Type:').grid(row=1, column=0, pady=5)
		self.radioButtonValue = IntVar()
		Radiobutton(top, text="Gesture", variable=self.radioButtonValue, value=0).grid(row=1, column=1, pady=5)
		Radiobutton(top, text="Fixed", variable=self.radioButtonValue, value=1).grid(row=1, column=2)

		#OK button to return to main screen
		Button(top, text='OK', command=self.send).grid(row=3, column=1, columnspan=2, pady=2)
		self.value = ''

	#Upon window closing, store values collected
	def send(self):
		if self.radioButtonValue.get() == 0:
			self.signType = 'Gesture'
		else:
			self.signType = 'Fixed'
		self.value = self.myEntryBox.get()
		self.top.destroy()


# Main application window
# --------------------------------------------------
class GUI:
	def __init__(self, master):
		self.master = master


		self.controller = Leap.Controller()
		sleep(0.01) #wait for leap controller to initiate
		self.vectorBuffer = []

		# Get exising dataset if exists, or start with a blank one
		if os.path.exists('dataset.p'):
			self.dataset = pickle.load(open("dataset.p", "rb"))
		else:
			self.dataset = []

		global dataset
		dataset = self.dataset

		#List and scrollbar for Signs
		self.signsScrollbar = Scrollbar(master)
		self.signsList = Listbox(master, yscrollcommand=self.signsScrollbar.set, exportselection=0)
		self.signsList.grid(row=0, rowspan=5, column=0, columnspan=2)
		self.signsList.bind('<<ListboxSelect>>', self.signsListBoxSelect)
		self.signsScrollbar.config(command=self.signsList.yview)
		self.signsScrollbar.grid(row=0, column=2, rowspan=5, sticky=N+S)

		#List and scrollbar for
		self.samplesScrollbar = Scrollbar(master)
		self.samplesList = Listbox(master, yscrollcommand=self.samplesScrollbar.set)
		self.samplesList.grid(row=0, rowspan=5, column=3, columnspan=2)
		self.samplesScrollbar.config(command=self.samplesList.yview)
		self.samplesScrollbar.grid(row=0, column=5, rowspan=5, sticky=N+S)

		#Buttons for controlling signs
		self.deleteSign = Button(master, text="Delete", command=self.deleteSign)
		self.deleteSign.grid(row=6, column=0)
		self.createSignButton = Button(master, text="New", command=self.createSign)
		self.createSignButton.grid(row=6, column=1)

		#Buttons for controlling samples
		self.deleteSampleButton = Button(master, text="Delete Last", command=self.deleteSample)
		self.deleteSampleButton.grid(row=6, column=3)
		self.recordButton = Button(master, text="Record")
		self.recordButton.bind("<Button-1>", self.startRecording)
		self.recordButton.bind("<ButtonRelease-1>", self.stopRecording)
		self.recordButton.grid(row=6, column=4)

		self.isRecording = False #Boolean for use by recorder thread
		self.updateSignsList() #Fill list of Signs
		self.currentSign = None #Sign selected


	def updateSignsList(self):
		self.signsList.delete(0, END)
		self.dataset = sorted(self.dataset, key=lambda x : x.value)
		for sign in self.dataset: #List in alphabetical order
			self.signsList.insert(END, ' '+sign.value)

	def updateSamplesList(self):
		if self.currentSign != None:
			self.samplesList.delete(0, END)
			for i in range(len(self.currentSign.samples)):
				self.samplesList.insert(END, ' '+str(i+1))
			self.samplesList.yview(END)
		else:
			self.samplesList.delete(0, END)

	def startRecording(self, event):
		self.vectorBuffer = []
		if self.controller.is_connected:
			if len(self.controller.frame().hands) != 0:
				if self.currentSign != None:
					self.isRecording = True
					thread = threading.Thread(target=self._record) #start recording
					thread.start()
				else:
					tkMessageBox.showwarning('','No sign selected')
			else:
				tkMessageBox.showwarning('','No hand in view')
		else:
			tkMessageBox.showwarning('','Leap Motion sensor not connected')

	def _record(self):
		while self.isRecording:
			if len(self.controller.frame().hands) != 0:
				hand = self.controller.frame().hands[0] #todo failure detection here
				self.vectorBuffer.append(hand)
				sleep(0.01)
			else:
				self.isRecording = False
				tkMessageBox.showwarning('','No hand in view')


	def stopRecording(self, event):
		if self.isRecording:
			value = self.currentSign
			self.isRecording = False #kill recording thread

			if self.currentSign.type == 'Fixed' and len(self.vectorBuffer):
				self.currentSign.samples.append(utils.vectorize(self.vectorBuffer, 1))

			elif len(self.vectorBuffer) >= 10: #make enough frames for 10 keyframes
				self.currentSign.samples.append(utils.vectorize(self.vectorBuffer, 10))

			else:
				tkMessageBox.showwarning('','No frames recorded')

			global dataset
			dataset = self.dataset #update global dataset for storing upon exit
			self.updateSamplesList()

	def createSign(self):
		inputDialog = SetNameDialog(self.master) #open dialog to set sign name
		self.master.wait_window(inputDialog.top)

		value = inputDialog.value #assure sign has name and is unique
		if len(value) > 0 and sum([1 for x in self.dataset if x.value == value]) == 0:
			self.currentSign = Sign(value, inputDialog.signType, [])  #create Sign object
			self.dataset.append(self.currentSign)
		self.updateSignsList()


	def deleteSign(self):
		selected = self.signsList.curselection()
		if len(selected) > 0:
			if tkMessageBox.askyesno("Delete", "Are you sure you want to delete this sign?"):
				self.currentSign = None
				del self.dataset[selected[0]]
				self.updateSignsList()
				self.updateSamplesList()

				global dataset #Update global dataset to save change on program exit
				dataset = self.dataset
		else:
			tkMessageBox.showwarning('','No sign selected')


	def deleteSample(self):
		selected = len(self.currentSign.samples)-1
		if selected >= 0:
			del self.currentSign.samples[selected]
			self.updateSamplesList()
			global dataset
			dataset = self.dataset
		else:
			tkMessageBox.showwarning('','No samples to delete')


	def signsListBoxSelect(self, event):
		selected = event.widget.curselection()
		if len(selected) > 0:
			self.currentSign = self.dataset[selected[0]]
		self.updateSamplesList()



# Initiate main application window
# --------------------------------------------------
root = Tk()
root.resizable(width=FALSE, height=FALSE)
root.wm_title("Builder")
app = GUI(root)
root.mainloop()


pickle.dump(dataset, open("dataset.p", "wb"))
