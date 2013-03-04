#!/opt/local/bin/python2.7
# encoding: utf-8

__author__ = "djt@mutablelogic.com (David Thorpe)"

# GAE imports
from google.appengine.ext import db, rdbms

# appengineapi_kit imports
from appengineapi_kit import api

class Connection:
	"""Class to connect to remote RDBMS"""
	def __init__(self,instance,database,user=None,password=None,charset='utf8'):
		self._params = { }
		self._params['instance'] = instance
		self._params['database'] = database
		self._params['charset'] = charset
		if user:
			self._params['user'] = user
		if password:
			self._params['password'] = password
		self._handle = None
	def connect(self,force_disconnect=False):
		if self._handle != None and force_disconnect:
			self.disconnect()
			assert self._handle==None
		params = self._params
		if self._handle==None:
			self._handle = rdbms.connect(**params)
	def disconnect(self):
		if self._handle:
			self._handle.close()
			self._handle = None

class DataModel(api.AbstractDataModel):
	pass

class Datastore(api.AbstractDataStore):
	""""Factory class which generates Google App Engine datastore model objects"""
	def get_model_class(self,name):
		assert isinstance(name,basestring) and len(name),"Datastore.get_model_class: Invalid model class name"
		# return a new model object
		model_class = type(name,(DataModel,),{ })
		return model_class
