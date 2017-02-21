'''
Written by Lennart Alexander Ornberg
for SCC300 Final Year Project
'''

import math

class NB:
	def __init__(self):
		'''
		Init classifier; per class store
		[mu, variance, log(sum(prior))+log(sum(base)), max euclidian dist.]
		'''
		self.classes = {}


	def train(self, dataset):
		'''
		Train classifier with dataset, where dataset is
		a list of tuples (label, vector)
		'''

		# Sort dataset by class
		classesData = {}
		for datapoint in dataset:
			# If class is new
			if datapoint[0] not in classesData:
				classesData[datapoint[0]] = [datapoint[1]]
				self.classes[datapoint[0]] = []

			# Append to existing class
			else:
				classesData[datapoint[0]].append(datapoint[1])

		# Compute formula components per class
		for _class, data in classesData.iteritems():
			prior = math.log(len(data)/float(len(dataset))) # P(x|c)
			mu = []
			variance = []

			# Fill lists of mu and variance for each feature
			for feature in zip(*data): # * selects columns instead of rows
				avg = sum(feature)/float(len(feature))
				mu.append(avg)
				variance.append(sum(map(lambda x : (x - avg) ** 2, feature)) / len(feature)) # TODO adjust for N-1 method?

			# Precompute first part of formula
			base = sum(map(lambda x : math.log(2 * math.pi * x), variance)) * (-0.5)

			# Get euclidian distance for sample furthes away from average
			maxDistance = 0
			totalDistance = 0
			for sample in data:
				euclid = self.euclidian(sample, mu)
				totalDistance += euclid
				if euclid > maxDistance:
					maxDistance = euclid

			# Store results
			self.classes[_class] = (mu, variance, prior + base, maxDistance)


	def euclidian(self, pVector, qVector):
		'''
		Get euclidian distance between vector p and q
		'''
		return math.sqrt(sum([(p - q) ** 2 for p, q in zip(pVector, qVector)]))


	def probabilities(self, vector):
		'''
		Get the logartihm of probabilities for all classes
		along with euclidian distances
		'''
		probabilities = []
		distances = [] #euclidian distances for novelty detection

		for _class in self.classes:
			_vars = zip(vector, self.classes[_class][0], self.classes[_class][1])

			# Calculate rest of formula; the exponent
			exp = (-0.5) * sum(map(lambda x : (x[0] - x[1])**2 / x[2], _vars))
			probabilities.append(self.classes[_class][2]+exp)

			# Calculate how many max distances vector is from average in n-dimensions
			distances.append(self.euclidian(vector, self.classes[_class][0]) / self.classes[_class][3])

		# Normalize; convert log to probability between 0 and 1
		_sum = sum(probabilities)
		output = []
		for _class, prob, dist in zip(self.classes, probabilities, distances):
			output.append((_class, (1 - (prob / _sum)) / 2.0, dist))

		return sorted(output, key=lambda x: x[1], reverse=True)


	def classify(self, vector):
		'''
		Get name only of the best candidate of class match
		'''
		return self.probabilities(vector)[0][0]


	def accuracy(self, dataset):
		'''
		Test accuracy of trained classifier
		'''
		return sum([d[0] == self.classify(d[1]) for d in dataset]) / float(len(dataset))
