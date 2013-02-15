#!/opt/local/bin/python2.7
# encoding: utf-8

__author__ = "djt@mutablelogic.com (David Thorpe)"

from appengineapi_kit import api

class RequestHandler(api.RequestHandler):

	def get_object(self,*path):
		return self.response_json(path)

	routes = (
		(api.RequestHandler.METHOD_GET,r"^/?([\w\/]*)$",get_object),
	)
