#!/opt/local/bin/python2.7
# encoding: utf-8

__author__ = "djt@mutablelogic.com (David Thorpe)"

from appengineapi_kit import api

class AddressBookEntry(api.Model):
	# MODEL NAME
	model_name = "AddressBookEntry"
	# PROPERTIES
	name = api.StringProperty(name='name',notnull=True,minlength=0,maxlength=100)
	email = api.StringProperty(name='email',notnull=False,minlength=0,maxlength=100)

class RequestHandler(api.RequestHandler):
	"""Implementation of the Address Book API"""

	def get_object(self,*path):
		"""Get AddressBookEntry object"""
		entry = AddressBookEntry(name="Fred Bloggs",email="fred@bloggs.com")
		return self.response_json(entry)

	models = (
		AddressBookEntry,
	)
	routes = (
		(api.RequestHandler.METHOD_GET,r"^/?([\w\/]*)$",get_object),
	)
