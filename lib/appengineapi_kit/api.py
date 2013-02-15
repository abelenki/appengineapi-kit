#!/opt/local/bin/python2.7
# encoding: utf-8

__author__ = "djt@mutablelogic.com (David Thorpe)"

# Python imports
import re

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

class RequestHandler(webapp2.RequestHandler):
	"""Class to handle generic AJAX requests"""

	# CONSTANTS
	METHOD_GET = 0
	METHOD_POST = 1
	METHOD_DELETE = 2
	METHOD_PUT = 3
	
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
	def _decode_request(self):
		"""Decode request body from JSON into a Python object"""
		try:
			if self.request.body:
				return simplejson.loads(self.request.body)
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
