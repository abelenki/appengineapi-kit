#!/opt/local/bin/python2.7
# encoding: utf-8

__author__ = "djt@mutablelogic.com (David Thorpe)"

# Python imports
import re, logging

# GAE imports
import webapp2, simplejson

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
		return { 'code': self.code, 'reason': self.reason }

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

class KeyProperty(ModelProperty):
	"""Key property for a model"""

	# PUBLIC METHODS
	def validate(self,name,value):
		"""Validate key value which should be a positive integer"""
		ModelProperty.validate(self,name,value)
		if value <= 0:
			raise ValueError("KeyProperty.validate: value should be positive integer")
		return value

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
	
class Model(object):
	"""Abstract Model class"""
	
	def __init__(self,**kwargs):
		self._properties = self._get_properties()
		self._values = { }
		self._key = KeyProperty()
		for (k,v) in self._properties.iteritems():
			if k in kwargs:
				self[k] = kwargs[k]
			else:
				self[k] = None

	@classmethod
	def _get_properties(self):
		""" Get all model properties as dictionary """
		properties = { }
		for name in vars(self):
			value = getattr(self,name)
			if isinstance(value,ModelProperty):
				properties[name] = value
		return properties

	def _get_property(self,name):
		return self._properties[name]

	@classmethod
	def get_model_name(self):
		"""Return name used to represent the model in communication"""
		if 'model_name' in vars(self):
			assert isinstance(self.model_name,basestring) and len(self.model_name),"Model.get_name: Invalid model_name"
			return self.model_name
		else:
			return self.__name__

	def set_key(self,value):
		self._values['_key'] = self._key.validate('_key',value)
	def get_key(self):
		return self._values.get('_key')
	key = property(get_key,set_key)

	def __setitem__(self,name,value):
		""" Set value for model object """
		model_property = self._get_property(name)
		self._values[name] = model_property.validate(name,value)
        
	def __getitem__(self,name):
		""" Get value for model object """
		return self._values[name]
		
	def as_json(self):
		"""Return model object as JSON with JSON-compliant values"""
		response = {
			'_type': self.get_model_name()
		}
		if self.key:
			response['_key'] = self.key
		for (k,p) in self._properties.iteritems():
			response[k] = p.as_json(self._values[k])
		return response

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
			for model in self.models:
				assert issubclass(model,Model)
				self._models[model.get_model_name()] = model
	# PRIVATE METHODS
	def _get_routes(self):
		"""Return tuple of routes"""
		if not 'routes' in vars(self.__class__):
			return None
		assert isinstance(self.routes,tuple) or isinstance(self.routes,list),"_get_routes: Invalid routes class property"
		return self.routes
	def _get_models(self):
		"""Return tuple of models"""
		if not 'models' in vars(self.__class__):
			return None
		assert isinstance(self.models,tuple) or isinstance(self.routes,list),"_get_models: Invalid models class property"
		return self.models
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
	def _decode_request_model(self,model,obj):
		"""Decode request body from JSON into a api.Model object"""
		raise HTTPException(HTTPException.STATUS_BADREQUEST,"Bad request of type %s" % model)
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
		elif isinstance(obj,Model):
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
