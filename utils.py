'''
Written by Lennart Alexander Ornberg
for SCC300 Final Year Project
'''

import Leap, math


# Main class for to link list of samples in database
# --------------------------------------------------
class Sign:
	def __init__(self, value, _type='Undefined', samples=[]):
		self.value = value
		self.type = _type #is either 'Fixed' or 'Gesture'
		self.samples = samples



# Compares to frames and determines if movement has occured or not
# --------------------------------------------------
def moving(handThen, handNow):
	total = []
	for x,y in zip(extractFeatures(handThen), extractFeatures(handNow)):
		total.append(abs(x-y))
	z = sum(total)/float(len(total))
	return z > 4.7 #hard coded threshold



# Takes a list of hand objects and returns a single vector
# of length 17 if fixed or 20x10 if gesture
# --------------------------------------------------
def vectorize(_buffer, size):
	if size == 1:
		return compress([extractFeatures(x) for x in _buffer], size)[:17]
	return compress(normalize([extractFeatures(x) for x in _buffer]), size)



# vector structure:
# xyz*fingers + hand roll + hand pitch + palm position*xyz
# where the three latter ones need to be normalized 
#(e.g start at 0)
def extractFeatures(hand):
	featureVector = []
	for finger in hand.fingers:
		normalized = finger.bone(3).center - hand.palm_position
		featureVector.extend((normalized.x, normalized.y, normalized.z))
	featureVector.append(math.degrees(hand.direction.pitch))
	featureVector.append(math.degrees(hand.direction.roll))
	palmPosition = hand.palm_position
	featureVector.extend((palmPosition.x, palmPosition.y, palmPosition.z))
	return featureVector



# Normalizes sequence of frames
# by starting palm position for frame 0
# at x, y and z value at 0
# --------------------------------------------------
def normalize(_buffer):
	startPoints = []
	output = []
	for i in range(15,20):
		startPoints.append(_buffer[0][i])
	for vector in _buffer:
		for i, j in zip(range(15,20), range(5)):
			vector[i] = vector[i]-startPoints[j]
		output.append(vector)
	return output



# Compress (average) sequence frames to fixed amount of keyframes
# --------------------------------------------------
def compress(_buffer, size):
	step = len(_buffer)/size
	output = []
	for i in range(size): #for each keyframe
		average = [0 for j in range(len(_buffer[0]))]	
		for vector in _buffer[i*step:(i+1)*step]:
			average = [q+w for q,w in zip(vector, average)]
		output.extend(map(lambda x : x/float(step), average))
	return output