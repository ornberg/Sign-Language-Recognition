'''
Written by Lennart Alexander Ornberg
for SCC300 Final Year Project
'''

import Leap, math

class Sign:
	'''
	Main class for to link list of samples in database
	'''
	def __init__(self, value, _type='Undefined', samples=[]):
		self.value = value
		self.type = _type # is either 'Fixed' or 'Gesture'
		self.samples = samples


def moving(handThen, handNow):
	'''
	Compares two frames and determine if movement has occured or not
	'''
	total = []
	for x, y in zip(extractFeatures(handThen), extractFeatures(handNow)):
		total.append(abs(x - y))
	z = sum(total) / float(len(total))

	# Hard coded threshold that seems to work alright to
	# see if difference should be deemed as movement or not
	return z > 4.7


def vectorize(_buffer, fixed):
	'''
	Takes a list of hand objects and returns a single vector
	of length 17 if fixed or 20x10 if gesture
	'''
	# If fixed sign
	if fixed:
		return compress([extractFeatures(x) for x in _buffer], 1)[:17]

	# If gesture sign
	return compress(normalize([extractFeatures(x) for x in _buffer]), 10)


def extractFeatures(hand):
	'''
	Extracts features from hand object and returns a feature vector of:
	XYZ position per finger, hand pitch in degrees, hand roll in degrees and
	the palms XYZ position
	'''
	featureVector = []
	# Get XYZ of each finger
	for finger in hand.fingers:
		normalized = finger.bone(3).center - hand.palm_position
		featureVector.extend((normalized.x, normalized.y, normalized.z))

	# Get pitch and roll
	featureVector.append(math.degrees(hand.direction.pitch))
	featureVector.append(math.degrees(hand.direction.roll))

	# Get XYZ of palm position
	palmPosition = hand.palm_position
	featureVector.extend((palmPosition.x, palmPosition.y, palmPosition.z))
	return featureVector


def normalize(_buffer):
	'''
	Normalizes sequence of frames by setting palms XYZ positions
	for first frame to 0 as origo, and all subsequent frames relative to that frame
	'''
	startPoints = []
	output = []
	for i in range(15,20):
		startPoints.append(_buffer[0][i])
	for vector in _buffer:
		for i, j in zip(range(15, 20), range(5)):
			vector[i] = vector[i] - startPoints[j]
		output.append(vector)
	return output


def compress(_buffer, size):
	'''
	Compress (average) sequence frames to fixed amount of keyframes
	so that frames of arbitrary length can be compared
	to other sequences
	'''
	# Determine how many frames need to be compressed to one keyframe
	step = len(_buffer)/size

	output = []
	for i in range(size): # for each keyframe
		average = [0 for j in range(len(_buffer[0]))]
		for vector in _buffer[i * step:(i + 1) * step]:
			average = [q + w for q, w in zip(vector, average)]
		output.extend(map(lambda x : x / float(step), average))
	return output


def validateFeatures(samples):
	'''
	Check that each feature across samples are not 0, to avoid a
	feature variance of 0, in turn causing a math domain error when doing log(0)
	'''
	for feature in zip(*samples):
		if not sum(feature):
			return False
	return True
