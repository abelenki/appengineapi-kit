#!/opt/local/bin/python2.7
# encoding: utf-8

__author__ = "djt@mutablelogic.com (David Thorpe)"

from appengineapi_kit import api

class AddressBookEntry(api.Model):
	# MODEL NAME
	model_name = "AddressBookEntry"
	# PROPERTIES
	name = api.StringProperty(notnull=True,minlength=0,maxlength=100)
	email = api.StringProperty(notnull=False,minlength=0,maxlength=100)

objects = (
	AddressBookEntry(name="Fred Bloggs",email="fred@bloggs.com"),
	AddressBookEntry(name="Joan Smith"),
	AddressBookEntry(name="Roger Jones",email="roger@hotmail.com")	
)

class RequestHandler(api.RequestHandler):
	"""Implementation of the Address Book API"""

	def get_object(self,*path):
		"""Get AddressBookEntry object"""
		return self.response_json(objects[1])

	models = (
		AddressBookEntry,
	)
	routes = (
		(api.RequestHandler.METHOD_GET,r"^/?([\w\/]*)$",get_object),
	)
