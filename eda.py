"""
Python class for clustering similar brands based on user favourites
v0.1
Author: Shivam Bansal
Creation Date: June 26, 2016
Last Updated on: June 26th, 2016
------------------------------------------------------------------------------------------------------

PREREQUISITE LIBRARIES:
'pymongo'         (for storing the matrix and jsons)
'time'            (for computing time)

-----------
DESCRIPTION
-----------
This file contains a class named Exploration which is designed to prepare dataset of shoppers 
and their favourite brands, conver the dataset into brand vs brand matrix, and calculate brand
similarity scores among them. The results are saved to mongo db, which are accessed using REST api 
built in flask.

----------------
EXAMPLE USE-CASES
-----------------

config = {
	'input_filename' : "brands_filtered.txt",
	"update_similarity_mapping" : True,
	"refresh_database" : True
}
Exploration(config)

"""


from pymongo import MongoClient 
import itertools, operator, time

__dbname__ = 'Similar'
__author__ = 'Shivam Bansal'

db = MongoClient()[__dbname__]

class Exploration:
	def __init__(self, config):
		"""
        Initializes all the parameters and build models.

        :type: json
        :param config: the input configurations for the model
        """

		self.input_file = config['input_filename']
		self.update_similarity_mapping = config['update_similarity_mapping']
		self.Model = Model() 
		if config['refresh_database']:
			self.Model.refresh_database() 
		
		start_time = time.time()
		print 
		print "Prepraing the dataset"
		self.user_brand_matrix, self.brand_mapper = self.prepare_dataset()
		print "Completed in --- %s seconds ---" % (time.time() - start_time)

		start_time = time.time()
		print 
		print "Creating Similarity Matrix"
		self.similarity_matrix = self.create_brand_similarity_matrix()
		print "Completed in --- %s seconds ---" % (time.time() - start_time)


		if self.update_similarity_mapping:
			start_time = time.time()
			print 
			print "Updating Database"
			self.update_similarity_matrix()
			print "Completed in --- %s seconds ---" % (time.time() - start_time)

	def prepare_dataset(self):
		"""
        Reads the input data, create brand id vs brand name mapping, user vs brand mapping. 
        """

		user_brand = {}
		brand_mapper = {}
		data = open(self.input_file).read().split("\n")
		for i,line in enumerate(data):
			row = line.split("\t")
			userId = row[0]
			brandId = row[1]
			brandName = row[2]

			''' Add Brands Mapping to DB'''			
			if brandId not in brand_mapper:
				brand_mapper[brandId] = brandName

			''' Create User-Brands Json '''
			if userId not in user_brand:
				user_brand[userId] = [] 
			user_brand[userId].append(brandId)
		return user_brand, brand_mapper

	def get_cartesian_pairs(self, lstA, lstB):
		"""
        Returns cartesian pairs in the form of list of list, from two lists. 
		Total N*(N-1)/2 cases are returned.

        :type list
        :param lstA: input list 1

        :type: list
        :param file_name: input list 2
        """

		pairs = [sorted(z) for z in list(itertools.product(lstA, lstB)) if z[0]!=z[1]]
		return list(pairs for pairs,_ in itertools.groupby(pairs))

	def create_brand_similarity_matrix(self):
		"""
        Calculates number of hits among two brands which occured together.
        """

		similarity_matrix = {}
		for x,y in self.user_brand_matrix.iteritems():

			''' Create cartesian product of items which occured together '''
			cartesian = self.get_cartesian_pairs(y, y)
			for pair in cartesian:
				if pair[0] not in similarity_matrix:
					similarity_matrix[pair[0]] = {}
				if pair[1] not in similarity_matrix[pair[0]]:
					similarity_matrix[pair[0]][pair[1]] = 0 
				similarity_matrix[pair[0]][pair[1]] += 1 
		return similarity_matrix

	def update_similarity_matrix(self):
		"""
       	Updates the similarity matrix into the database.
        """
		for bid, similar in self.similarity_matrix.iteritems():
			for simid, score in similar.iteritems():
				similarBrandName = self.brand_mapper.get(simid)
				brandName = self.brand_mapper.get(bid)
				doc = { '_id' : bid+" "+simid, 'brandId' : bid, 'similarId' : simid, 'score' : score, 
						'brandName' : brandName, 'similarBrandName': similarBrandName}
				self.Model.push_data(document = doc, collection_name = "BrandSimilarity")


class Model:
	def push_data(self, document = {}, collection_name = "test"):
		"""
        Adds data to mongodb

        :type: json
        :param document: document to be inserted into the database

        :type: string
        :param collection_name: name of the collection
        """

		try:
			db[collection_name].insert(document)
		except Exception as E:
			print "Already Present", E

	def get_most_similar(self, brandId, limit):
		"""
        Aggregator function to return the similar pairs, based on similarity score

        :type: String
        :param brandId: ID of the input brand

        :type: int
        :param limit: number of similar brands to be outputed
        """

		pipeline = [{'$match' : {'brandId' : brandId}}, {'$sort' : {'score' : -1}}, {'$limit': limit}]
		result = db['BrandSimilarity'].aggregate(pipeline)
		result = [x for x in result if x['score'] >= 30]
		return result 
		
	def refresh_database(self):
		"""
        Drops everything from the database
        """

		for cname in db.collection_names():
			if cname != "system.indexes":
				db[cname].drop()


if __name__ == '__main__':
	config = {
		'input_filename' : "brands_filtered.txt",
		"update_similarity_mapping" : True,
		"refresh_database" : True
	}
	Exploration(config)