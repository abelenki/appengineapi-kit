#!/opt/local/bin/python2.7
# encoding: utf-8

__author__ = "djt@mutablelogic.com (David Thorpe)"

# GAE imports
import webapp2
from django.utils import simplejson

class RequestHandler(webapp2.RequestHandler):
	# Response handlers
	def response_json(self,code=200,obj=None):
		assert isinstance(code,int)
		self.error(code)
		self.response.headers['Content-Type'] = "application/json"
		self.response.write(simplejson.dumps(obj))
		self.response.write("\n")

	# Request handlers
	#  GET handler - retrieve data
	def get(self,*path):
		self.response_json(obj=path)
	#  POST handler - create data
	def post(self,path):
		self.response_json(obj=path)
	# DELETE handler - delete data
	def delete(self,path):
		self.response_json(obj=path)
	# PUT handler - update data
	def put(self,path):
		self.response_json(obj=path)
