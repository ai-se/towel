"""
This is a sample elasticsearch injection framework

"""

from __future__ import print_function, division
import elasticsearch
import requests
from pdb import set_trace

class es_test:
	def __init__(self):
		self.es = elasticsearch.Elasticsearch()  # use default of localhost, port 9200

	def save(self):
		# Return a response of the top 100 IAMA Reddit posts of all time
		response = requests.get("http://api.reddit.com/r/iama/top/?t=all&limit=100",
		                        headers={"User-Agent":"TrackMaven"})

		fields = ['title', 'selftext', 'author', 'score',
		        'ups', 'downs', 'num_comments', 'url', 'created']

		# Loop through results and add each data dictionary to the ES "reddit" index
		for i, iama in enumerate(response.json()['data']['children']):
		    content = iama['data']
		    doc = {}
		    for field in fields:
		        doc[field] = content[field]
		    self.es.index(index="reddit", doc_type='iama', id=i, body=doc)

	def query(self):
		# Fetch a specific result
		res = self.es.get(index='reddit', doc_type='iama', id=1)
		# print(res['_source'])

		# Update the index to be able to query against it
		self.es.indices.refresh(index="reddit")

		# Query for results: noVessel will match this author
		res = self.es.search(index="reddit",
                body={"query": {"match": {"author": "no results here!"}}})
		print(res['hits']['total'])

		# Query based on title text
		res = self.es.search(index='reddit', body={"query": {"match": {"title": "obama"}}})
		print (res['hits']['total'])
		print (res['hits']['hits'][0]['_source']['title'])


if __name__=="__main__":
	es_test().query()
