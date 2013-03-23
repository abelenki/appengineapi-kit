#!/opt/local/bin/python2.7
# encoding: utf-8

__author__ = "djt@mutablelogic.com (David Thorpe)"

# GAE imports
from google.appengine.ext import db

# appengineapi_kit imports
from appengineapi_kit import api,query

class Select(query.Select):
	"""Implements specific methods for the query/select for App Engine datastore"""
	def run(self,limit):
		# obtain an empty feed object
		feed = super(Select,self).run(limit)
		# run the query
		bindings = self.bindings()
		items = db.GqlQuery(self.as_sql(),*bindings).run(limit=limit)
		# return the feed
		return feed

class DataModel(db.Expando,api.AbstractDataModel):
	""""Implements the Google App Engine datastore model object"""
	__value = { }
	def __setitem__(self,name,value):
		setattr(self,name,value)
	def __getitem__(self,name):
		return getattr(self,name)
	@classmethod
	def get_by_primary_key(self,key):
		assert (isinstance(key,int) or isinstance(key,long)),"DatastoreModel.get_by_primary_key: Invalid key type"
		assert key > 0,"DatastoreModel.get_by_primary_key: Invalid key value"
		return self.get_by_id(key)
	def put(self):
		return super(db.Expando,self).put()
	def delete(self):
		assert self.is_saved()==True,"DatastoreModel.update: Calling update on new object"
		super(db.Expando,self).delete()
	def primary_key(self):
		return super(db.Expando,self).key().id()

class DataStore(api.AbstractDataStore):
	""""Factory class which generates Google App Engine datastore model objects"""
	def get_model_class(self):
		# return a new model object
		entity_name = self.get_entity_name()
		model_class = type(entity_name,(DataModel,),{ })
		return model_class
	def get_select(self,model,**kwargs):
		return Select(model,**kwargs)

