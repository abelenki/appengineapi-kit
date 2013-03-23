#!/opt/local/bin/python2.7
# encoding: utf-8

__author__ = "djt@mutablelogic.com (David Thorpe)"

import appengineapi_kit.api

class Feed(object):
	def __init__(self,model,limit=None):
		assert issubclass(model,appengineapi_kit.api.Model)
		assert limit==None or (isinstance(limit,(int,long)) and limit > 0)
		self._model = model
		self._limit = limit
	def as_json(self):
		"""Return feed object as JSON with JSON-compliant values"""
		response = {
			'_type': self._model.get_kind(),
			'limit': self._limit,
			'items': [ ]
		}
		return response
		
class Query(object):
	def __init__(self,model):
		assert issubclass(model,appengineapi_kit.api.Model)
		self._model = model
	def execute(self,limit=None):
		assert limit==None or (isinstance(limit,(int,long)) and limit > 0)
		feed = Feed(self._model,limit=limit)
		return feed
		