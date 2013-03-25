#!/opt/local/bin/python2.7
# encoding: utf-8

__author__ = "djt@mutablelogic.com (David Thorpe)"

# appengineapi-kit imports
import appengineapi_kit.query

# ABSTRACTIONS

class AbstractDataStore(object):
	def __init__(self,entity_name):
		assert isinstance(entity_name,basestring),"AbstractDataStore.__init__: Missing entity_name parameter"
		self._entity_name = entity_name
	def get_model_class(self):
		raise Exception("AbstractDataStore.get_model_class: Calling abstract method")
	def get_entity_name(self):
		return self._entity_name

class AbstractDataModel(object):
	def __setitem__(self,name,value):
		raise Exception("AbstractDataModel.__setitem__: Calling abstract method")
	def __getitem__(self,name):
		raise Exception("AbstractDataModel.__getitem__: Calling abstract method")
	@classmethod
	def get_by_primary_key(self,key):
		raise Exception("AbstractDataModel.get_by_primary_key: Calling abstract method")
	def get_select(self,model,**kwargs):
		raise Exception("AbstractDataModel.get_select: Calling abstract method")
	def put(self):
		raise Exception("AbstractDataModel.put: Calling abstract method")
	def delete(self):
		raise Exception("AbstractDataModel.delete: Calling abstract method")
	def primary_key(self):
		raise Exception("AbstractDataModel.primary_key: Calling abstract method")

# PROPERTIES

class ModelProperty(object):
	"""Abstract Model Property class"""

	def __init__(self,notnull=None):
		self._notnull = notnull
	
	# PUBLIC METHODS
	def validate(self,name,value):
		""" Return validated version of a value, or raise an error """
		if value==None and self._notnull:
			raise ValueError("ModelProperty.validate: Value cannot be NULL for property '%s'" % name)
		return value
	def as_json(self,value):
		"""Return JSON-compliant value"""
		if type(value) in (basestring,bool,int,long):
			return value
		return "%s" % value

class StringProperty(ModelProperty):
	"""String Model Property class"""
	
	def __init__(self,minlength=None,maxlength=None,**kwargs):
		ModelProperty.__init__(self,**kwargs)
		self._minlength = minlength
		self._maxlength = maxlength

	# PUBLIC METHODS
	def validate(self,name,value):
		"""Validate string value against property"""
		ModelProperty.validate(self,name,value)
		if value and isinstance(value,basestring) != True:
			raise ValueError("StringProperty.validate: Not a string for property '%s'" % name)
		if value and self._minlength != None and len(value) < self._minlength:
			raise ValueError("StringProperty.validate: MINLENGTH condition fails for property '%s'" % name)
		if value and self._maxlength != None and len(value) > self._maxlength:
			raise ValueError("StringProperty.validate: MAXLENGTH condition fails for property '%s'" % name)
		return value

class IntegerProperty(ModelProperty):
	"""Integer Model Property class"""
	
	def __init__(self,minvalue=None,maxvalue=None,**kwargs):
		ModelProperty.__init__(self,**kwargs)
		self._minvalue = minvalue
		self._maxvalue = maxvalue

	# PUBLIC METHODS
	def validate(self,name,value):
		"""Validate int or long value against property"""
		ModelProperty.validate(self,name,value)
		if value and (isinstance(value,int) or isinstance(value,long)) != True:
			raise ValueError("IntegerProperty.validate: Not an integer for property '%s'" % name)
		if value and self._minvalue != None and value < self._minvalue:
			raise ValueError("IntegerProperty.validate: MINVALUE condition fails for property '%s'" % name)
		if value and self._maxvalue != None and value > self._maxvalue:
			raise ValueError("IntegerProperty.validate: MAXVALUE condition fails for property '%s'" % name)
		return value

# MODEL

class Model(object):
	"""Abstract Model class"""
	def __init__(self,**kwargs):
		self.__properties = self._get_properties()
		self.__proxy_class = self._get_model_proxy_factory().get_model_class()
		if '_proxy' in kwargs:
			# proxy object already contains values
			self.__proxy = kwargs['_proxy']
		else:
			# set values from arguments
			self.__proxy = (self.__proxy_class)()
			for (k,v) in self.__properties.iteritems():
				if k in kwargs:
					self[k] = kwargs[k]
				else:
					self[k] = None
	@classmethod
	def _get_model_proxy_factory(self):
		"""Return proxy factory object, which can generate concrete proxy models"""
		assert 'proxy' in vars(self),"Model._get_model_proxy_factory: missing proxy property"
		assert isinstance(self.proxy,AbstractDataStore),"Model._get_model_proxy_factory: proxy needs to be subclass of AbstractDataStore"
		return self.proxy
	@classmethod
	def _get_properties(self):
		""" Get all model properties as dictionary """
		properties = { }
		for name in vars(self):
			value = getattr(self,name)
			if isinstance(value,ModelProperty):
				properties[name] = value
		return properties
	@classmethod
	def get_kind(self):
		"""Return name used to represent the model"""
		return self._get_model_proxy_factory().get_entity_name()
	@classmethod
	def get_select(self,**kwargs):
		"""Return select statement used to represent the model"""
		return self._get_model_proxy_factory().get_select(self,**kwargs)
	def key(self):
		return self.__proxy.primary_key()
	def is_saved(self):
		return self.__proxy.is_saved()
	def __setitem__(self,name,value):
		""" Set value for model object """
		model_property = self.__properties[name]
		self.__proxy[name] = model_property.validate(name,value)
	def __getitem__(self,name):
		""" Get value for model object """
		return self.__proxy[name]
	def as_json(self):
		"""Return model object as JSON with JSON-compliant values"""
		response = {
			'_type': self.get_kind()
		}
		if self.key():
			response['_key'] = self.key()
		for (k,p) in self.__properties.iteritems():
			response[k] = p.as_json(self.__proxy[k])
		return response
	def put(self):
		"""Store object in data store"""
		return self.__proxy.put()
	def delete(self):
		"""Delete object from the data store"""
		return self.__proxy.delete()
	def update(self,values):
		assert isinstance(values,dict)
		all_keys = values.keys()
		# translate values
		for (name,prop) in self.__properties.iteritems():
			if name in values:
				values[name] = prop.validate(name,values[name])
				all_keys.remove(name)
		if len(all_keys):
			raise TypeError("Model.update: invalid update data: %s" % ", ".join(all_keys))
		# update object with values
		for (name,prop) in self.__properties.iteritems():
			if name in values:
				self.__proxy[name] = values[name]
		# put the entity back to datastore
		self.put()
	@classmethod
	def get_by_key(self,key):
		"""Retrieve object from the data store by key"""
		proxy = self.proxy.get_model_class().get_by_primary_key(key)
		if proxy:
			return (self)(_proxy=proxy)
		else:
			return None
	@classmethod
	def get_query(self):
		"""Return query object"""
		return appengineapi_kit.query.Query(self)
