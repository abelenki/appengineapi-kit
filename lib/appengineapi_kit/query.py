#!/opt/local/bin/python2.7
# encoding: utf-8

__author__ = "djt@mutablelogic.com (David Thorpe)"

# python imports
import logging

# local imports
import appengineapi_kit.api
import appengineapi_kit.models

class Select(object):
	def __init__(self,model):
		assert issubclass(model,appengineapi_kit.models.Model)
		self._model = model
	def bindings(self):
		return [ ]
	def as_sql(self):
		return "SELECT %s FROM %s" % ("*",self._model.get_kind())
	def run(self,limit=None):
		return Feed(self._model,limit)

class Feed(object):
	def __init__(self,model,limit=None):
		assert issubclass(model,appengineapi_kit.models.Model)
		assert limit==None or (isinstance(limit,(int,long)) and limit > 0)
		self._model = model
		self._limit = limit
		self._items = [ ]

	# PROPERTIES
	def get_items(self):
		return self._items
	def set_items(self,value):
		assert isinstance(value,(list,tuple)),"items cannot be of type %s" % type(value).__name__
		items = [ ]
		for item in value:
			assert isinstance(value,self._model)
			items.append(item)
		self._items = items
	items = property(get_items,set_items)
	
	# METHODS
	def append(self,value):
		assert isinstance(value,self._model)
		self._items.append(value)
	def as_json(self):
		"""Return feed object as JSON with JSON-compliant values"""
		response = {
			'_type': self._model.get_kind(),
			'limit': self._limit,
			'items': [ item.as_json() for item in self.items ],
			'count': len(self.items)
		}
		return response

class Query(object):
	def __init__(self,model):
		assert issubclass(model,appengineapi_kit.models.Model)
		self._model = model
	def execute(self,limit=None):
		assert limit==None or (isinstance(limit,(int,long)) and limit > 0)
		return self._model.get_select().run(limit=limit)
