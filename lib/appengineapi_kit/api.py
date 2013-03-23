#!/opt/local/bin/python2.7
# encoding: utf-8

__author__ = "djt@mutablelogic.com (David Thorpe)"

# Python imports
import re, logging

# GAE imports
import webapp2
from django.utils import simplejson

# appengineapi-kit imports
from appengineapi_kit import query, model

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
				assert issubclass(model,model.Model)
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
		if model==None or not issubclass(model,model.Model):
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
		elif isinstance(obj,(model.Model,query.Feed)):
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
