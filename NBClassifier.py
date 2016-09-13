'''
Written by Lennart Alexander Ornberg
for SCC300 Final Year Project
'''

import math, utils

class NB:
	def __init__(self):
		self.classes = {} # class : [mu..], [variance..], log(sum(prior))+log(sum(base)), furthest euclidian distance

	#Train classifier with dataset, where dataset is a list of tuples (label, vector)
	def train(self, dataset):
		#Sort dataset by class
		classesData = {}
		for datapoint in dataset:
			if datapoint[0] not in classesData:
				classesData[datapoint[0]] = [datapoint[1]]
				self.classes[datapoint[0]] = []
			else:
				classesData[datapoint[0]].append(datapoint[1])

		#Compute formula components per class
		for _class, data in classesData.iteritems():	
			prior = math.log(len(data)/float(len(dataset))) #P(x|c)
			mu = []
			variance = []

			#Fill lists of mu and variance for each feature
			for feature in zip(*data): # asterisk selects columns instead of rows
				avg = sum(feature)/float(len(feature))
				mu.append(avg)
				variance.append(sum(map(lambda x : (x-avg)**2, feature)) / len(feature)) #TODO adjust for N-1 method?

			#Precompute first part of formula
			base = sum(map(lambda x : math.log(2 * math.pi * x), variance)) * (-0.5)

			#Get euclidian distance for sample furthes away from average
			maxDistance = 0
			totalDistance = 0
			for sample in data:
				euclid = self.euclidian(sample,mu)
				totalDistance += euclid
				if euclid > maxDistance:
					maxDistance = euclid

			self.classes[_class] = (mu, variance, prior+base, maxDistance) #store results

	def euclidian(self, pVector, qVector):
		return math.sqrt(sum([(p-q)**2 for p,q in zip(pVector,qVector)]))

	#Get log of probabilities for classes
	def probabilities(self, vector):
		probabilities = []
		distances = [] #euclidian distances for novelty detection

		for _class in self.classes:
			_vars = zip(vector, self.classes[_class][0], self.classes[_class][1])
			exp = (-0.5) * sum(map(lambda x : (x[0] - x[1])**2 / x[2], _vars)) #rest of formula
			probabilities.append(self.classes[_class][2]+exp)
			distances.append(self.euclidian(vector,self.classes[_class][0]) / self.classes[_class][3])
			#Calculate how many max distances vector is from average in n-dimensions

		#Normalizing; converting log to probability between 0 and 1
		_sum = sum(probabilities)
		output = []
		for _class, prob, dist in zip(self.classes, probabilities, distances):
			output.append(( _class, (1-(prob/_sum))/2.0, dist))

		return sorted(output, key=lambda x:x[1], reverse=True)

	#Get just the name of the esimated class for a feature vector
	def classify(self, vector):
		return self.probabilities(vector)[0][0]

	#Test accuracy of trained classifier
	def accuracy(self, dataset):
		return sum([d[0] == self.classify(d[1]) for d in dataset])/float(len(dataset))



