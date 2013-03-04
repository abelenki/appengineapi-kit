#!/opt/local/bin/python2.7
# encoding: utf-8

__author__ = "djt@mutablelogic.com (David Thorpe)"

# GAE imports
from google.appengine.ext import db

# appengineapi_kit imports
from appengineapi_kit import api

class DatastoreModel(db.Expando):
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

class Datastore(api.AbstractDatastore):
	""""Factory class which generates Google App Engine datastore model objects"""
	def get_model_class(self,name):
		assert isinstance(name,basestring) and len(name),"Datastore.get_model_class: Invalid model class name"
		# return a new model object
		model_class = type(name,(DatastoreModel,),{ })
		return model_class
