#!/opt/local/bin/python2.7
# encoding: utf-8

__author__ = "djt@mutablelogic.com (David Thorpe)"

# Python imports
import re, logging

# GAE imports
import webapp2
from django.utils import simplejson

# Local imports
from appengineapi_kit import query

class HTTPException(Exception):
	""" HTTP specific error response """
	
	STATUS_OK = 200
	STATUS_BADREQUEST = 400
	STATUS_NOTFOUND = 404
	STATUS_SERVERERROR = 500
	
	REASONS = {
		STATUS_OK: "OK",
		STATUS_BADREQUEST: "Bad Request",
		STATUS_NOTFOUND: "Resource not found",
		STATUS_SERVERERROR: "Server Error"
	}
	
	def __init__(self,code,reason=None):
		self._code = code
		self._reason = reason
	
	# PROPERTIES
	def get_code(self):
		return self._code
	code = property(get_code)

	def get_reason(self):
		if self._reason:
			return self._reason
		if self._code in REASONS:
			return REASONS[self._code]
		return "Error Code %s" % self.code
	reason = property(get_reason)
	
	# PUBLIC METHODS
	def as_json(self):
		return { '_type': type(self).__name__, 'code': self.code, 'reason': self.reason }

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
	def put(self):
		raise Exception("AbstractDataModel.put: Calling abstract method")
	def delete(self):
		raise Exception("AbstractDataModel.delete: Calling abstract method")
	def primary_key(self):
		raise Exception("AbstractDataModel.primary_key: Calling abstract method")
	
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
		return query.Query(self)

class RequestHandler(webapp2.RequestHandler):
	"""Class to handle generic AJAX requests"""

	# CONSTANTS
	METHOD_GET = 0
	METHOD_POST = 1
	METHOD_DELETE = 2
	METHOD_PUT = 3
	
	# CONSTRUCTOR
	def __init__(self,*args):
		webapp2.RequestHandler.__init__(self,*args)
		# make hash of models which are handled by the API
		self._models = { }
		if 'models' in vars(self.__class__):
			assert isinstance(self.models,tuple) or isinstance(self.models,list),"RequestHandler.__init__: invalid 'models' property"
			for model in self.models:
				assert issubclass(model,Model)
				model_name = model.get_kind()
				if model_name in self._models:
					raise ValueError("Two models with same name '%s'" % model_name)
				self._models[model_name] = model
	# PRIVATE METHODS
	def _get_routes(self):
		"""Return tuple of routes"""
		if not 'routes' in vars(self.__class__):
			return None
		assert isinstance(self.routes,tuple) or isinstance(self.routes,list),"_get_routes: Invalid routes class property"
		return self.routes
	def _decode_method(self):
		"""Decode the method into constants"""
		if self.request.method=='GET':
			return RequestHandler.METHOD_GET
		if self.request.method=='POST':
			return RequestHandler.METHOD_POST
		if self.request.method=='DELETE':
			return RequestHandler.METHOD_DELETE
		if self.request.method=='PUT':
			return RequestHandler.PUT
		return None
	def _decode_request_model(self,model_name,json):		
		"""Decode request body from JSON into a api.Model object"""
		assert isinstance(json,dict),"_decode_request_model: Invalid json argument"
		model = self._models.get(model_name)
		if model==None or not issubclass(model,Model):
			raise HTTPException(HTTPException.STATUS_BADREQUEST,"Bad request of type '%s'" % model_name)
		return (model)(**json)
	def _decode_request(self):
		"""Decode request body from JSON into a Python object"""
		try:
			if self.request.body:
				request = simplejson.loads(self.request.body)
				if(isinstance(request,dict) and request.get('_type')):
					request = self._decode_request_model(request.get('_type'),request)
				return request
			else:
				return None
		except simplejson.JSONDecodeError, e:
			raise HTTPException(HTTPException.STATUS_BADREQUEST,"Bad request: %s" % e)
		except KeyError, e:
			raise HTTPException(HTTPException.STATUS_BADREQUEST,"Bad request: %s" % e)

	# PUBLIC METHODS
	def response_json(self,obj):
		"""Send response to client"""
		self.response.headers['Content-Type'] = "application/json"
		if isinstance(obj,HTTPException):
			self.error(obj.code)
			self.response.write(simplejson.dumps(obj.as_json()))
		elif type(obj) in (basestring,bool,int,long,list,tuple,dict):
			self.response.write(simplejson.dumps(obj))
		elif isinstance(obj,(Model,query.Feed)):
			self.response.write(obj.as_json())
		else:
			e = HTTPException(code=HTTPException.STATUS_SERVERERROR,reason="Invalid response object: %s" % type(obj).__name__)
			self.error(e.code)
			self.response.write(simplejson.dumps(e.as_json()))
		self.response.write("\n")
	def route_request(self,method,path):
		"""Call appropriate matched route for web request"""
		assert isinstance(method,int) or isinstance(method,long),"route_request: Unexpected method"
		assert isinstance(path,basestring),"route_request: Unexpected path"
		for route in self._get_routes():
			assert isinstance(route,tuple) or isinstance(route,list),"route_request: Invalid route"
			assert len(route) >= 3,"route_request: Invalid route"
			# skip route if not correct method
			if route[0] != method: continue
			# match route to path
			m = re.match(route[1],path)
			if not m: continue
			# get route arguments
			args = list(m.groups())
			# where requests are POST or PUT, append the JSON body to the arguments
			if method in (RequestHandler.METHOD_POST,RequestHandler.METHOD_PUT):
				args.append(self._decode_request())
			# call routing method
			return route[2](self,*args)
		raise HTTPException(HTTPException.STATUS_NOTFOUND,reason="Not found, unknown path: %s" % path)
	def get(self,path):
		"""GET handler - get data"""
		try:
			self.route_request(RequestHandler.METHOD_GET,path)
		except HTTPException,e:
			self.response_json(e)
	def post(self,path):
		"""POST handler - create data"""
		try:
			self.route_request(RequestHandler.METHOD_POST,path)
		except HTTPException,e:
			self.response_json(e)
	def delete(self,path):
		"""delete handler - delete data"""
		try:
			self.route_request(RequestHandler.METHOD_DELETE,path)
		except HTTPException,e:
			self.response_json(e)
	def put(self,path):
		"""PUT handler - update data"""
		try:
			self.route_request(RequestHandler.METHOD_PUT,path)
		except HTTPException,e:
			self.response_json(e)
