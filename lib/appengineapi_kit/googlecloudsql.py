#!/opt/local/bin/python2.7
# encoding: utf-8

__author__ = "djt@mutablelogic.com (David Thorpe)"

# GAE imports
from google.appengine.ext import db

# appengineapi_kit imports
from appengineapi_kit import api

class DatastoreModel(object):
	pass

class Datastore(api.AbstractDatastore):
	""""Factory class which generates Google App Engine datastore model objects"""
	def get_model_class(self,name):
		assert isinstance(name,basestring) and len(name),"Datastore.get_model_class: Invalid model class name"
		# return a new model object
		model_class = type(name,(DatastoreModel,),{ })
		return model_class
