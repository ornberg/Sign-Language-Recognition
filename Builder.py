import Leap
import sys, thread, time, random, math, os
import threading
from time import sleep
import pickle
from Tkinter import *
import tkMessageBox
import utils

Sign = utils.Sign
dataset = []

class SetNameDialog:
	def __init__(self, parent):
		top = self.top = Toplevel(parent)
		top.wm_title("New Sign")

		Label(top, text='Word:').grid(row=0, pady=5)
		self.myEntryBox = Entry(top)
		self.myEntryBox.grid(row=0, column=1, columnspan=3)

		Label(top, text='Type:').grid(row=1, column=0, pady=5)
		self.radioButtonValue = IntVar()
		Radiobutton(top, text="Gesture", variable=self.radioButtonValue, value=0).grid(row=1, column=1, pady=5)
		Radiobutton(top, text="Fixed", variable=self.radioButtonValue, value=1).grid(row=1, column=2)

		Button(top, text='OK', command=self.send).grid(row=3, column=1, columnspan=2, pady=2)
		self.value = ''

	def send(self):
		if self.radioButtonValue.get() == 0:
			self.signType = 'Gesture'
		else:
			self.signType = 'Fixed'
		self.value = self.myEntryBox.get()
		self.top.destroy()


class GUI:
	def __init__(self, master):
		self.master = master

		#Not working properly
		#self.master.bind('<KeyPress-space>', self.handleSpacebar)
		if os.path.exists('dataset.p'):
			self.dataset = pickle.load(open("dataset.p", "rb"))
		else:
			self.dataset = []

		global dataset
		dataset = self.dataset

		self.controller = Leap.Controller()
		self.vectorBuffer = []
		self.currentSign = None

		#Frame holding lists and scrollbars
		self.signsScrollbar = Scrollbar(master)
		self.signsList = Listbox(master, yscrollcommand=self.signsScrollbar.set, exportselection=0)
		self.signsList.grid(row=0, rowspan=5, column=0, columnspan=2)
		self.signsList.bind('<<ListboxSelect>>', self.signsListBoxSelect)
		self.signsScrollbar.config(command=self.signsList.yview)
		self.signsScrollbar.grid(row=0, column=2, rowspan=5, sticky=N+S)

		self.samplesScrollbar = Scrollbar(master)
		self.samplesList = Listbox(master, yscrollcommand=self.samplesScrollbar.set)
		self.samplesList.grid(row=0, rowspan=5, column=3, columnspan=2)
		self.samplesScrollbar.config(command=self.samplesList.yview)
		self.samplesScrollbar.grid(row=0, column=5, rowspan=5, sticky=N+S)

		self.updateSignsList()

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

		self.isRecording = False

	#Not working properly (sends sequence of press when it is in fact held down)
	#def handleSpacebar(self, event):
	#	if self.isRecording == False:
	#		self.startRecording(None)
	#	else:
	#		self.stopRecording(None)

	def updateSignsList(self):
		# Delete existing entries in list
		self.signsList.delete(0, END)

		# Fill list alphabetically
		self.dataset = sorted(self.dataset, key=lambda x : x.value)
		for sign in self.dataset: #List in alphabetical order
			self.signsList.insert(END, ' ' + sign.value)

	def updateSamplesList(self):
		if self.currentSign != None:
			self.samplesList.delete(0, END)
			for i in range(len(self.currentSign.samples)): #Todo, if empty
				self.samplesList.insert(END, ' '+str(i+1))
			self.samplesList.yview(END)

	def startRecording(self, event):
		self.vectorBuffer = []
		if self.controller.is_connected:
			if self.currentSign != None:
				self.isRecording = True
				thread = threading.Thread(target=self._record)
				thread.start()
			else:
				tkMessageBox.showwarning('','No sign selected')
		else:
			tkMessageBox.showwarning('','Leap Motion sensor not connected')

	def _record(self):
		while self.isRecording:
			hand = self.controller.frame().hands[0] #TODO failure detection
			self.vectorBuffer.append(hand)
			sleep(0.01)

	# Not in use, better to let user specify if sign is fixed or a gesture,
	# instead of detecting it automatically
	def isGesture(self, _buffer):
		gesture = 0
		fixed = 0
		for i in range(10,len(_buffer)+1,10):
			if utils.moving(_buffer[i-10],_buffer[i-1]):
				gesture += 1
			else:
				fixed -= 0
		return gesture > fixed


	def stopRecording(self, event):
		if self.isRecording:
			value = self.currentSign
			self.isRecording = False

			if self.currentSign.type == 'Fixed':
				self.currentSign.samples.append(utils.vectorize(self.vectorBuffer, 1))
			elif len(self.vectorBuffer) >= 10: #TODO rename vectorbuffer to framebuffer
				self.currentSign.samples.append(utils.vectorize(self.vectorBuffer, 10))

			global dataset
			dataset = self.dataset
			self.updateSamplesList()

	def createSign(self):
		inputDialog = SetNameDialog(self.master)
		self.master.wait_window(inputDialog.top)

		value = inputDialog.value
		# Add sign to list if name has lenght and is not equal to existing signs
		if len(value) > 0 and sum([1 for x in self.dataset if x.value == value]) == 0:
			self.currentSign = Sign(value, inputDialog.signType, [])
			self.dataset.append(self.currentSign)
		self.updateSignsList()


	def deleteSign(self):
		selected = self.signsList.curselection()
		if len(selected) > 0:
			if tkMessageBox.askyesno("Delete", "Are you sure you want to delete this sign?"):
				del self.dataset[selected[0]]
				self.updateSignsList()
				global dataset
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




root = Tk()
root.resizable(width=FALSE, height=FALSE)
root.wm_title("Builder")
app = GUI(root)
root.mainloop()


pickle.dump(dataset, open("dataset.p", "wb"))
