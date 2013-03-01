#!/opt/local/bin/python2.7
# encoding: utf-8

__author__ = "djt@mutablelogic.com (David Thorpe)"

from appengineapi_kit import api
import logging

class AddressBookEntry(api.Model):
	# MODEL NAME
	model_name = "AddressBookEntry"
	# PROPERTIES
	name = api.StringProperty(notnull=True,minlength=0,maxlength=100)
	email = api.StringProperty(notnull=False,minlength=0,maxlength=100)

class RequestHandler(api.RequestHandler):
	"""Implementation of the Address Book API"""

	def get_object(self,model_name,key):
		"""Get AddressBookEntry object"""
		if model_name != "AddressBookEntry":
			raise api.HTTPException(api.HTTPException.STATUS_BADREQUEST,"Bad request, expecting AddressBookEntry")
		entry = AddressBookEntry.get_by_key(long(key))
		if not entry:
			raise api.HTTPException(api.HTTPException.STATUS_NOTFOUND,"No AddressBookEntry object with key %s" % key)
		assert isinstance(entry,AddressBookEntry)
		return self.response_json(entry)
	def create_object(self,path,entry):
		"""Create new AddressBookEntry object"""
		if not isinstance(entry,AddressBookEntry):
			raise api.HTTPException(api.HTTPException.STATUS_BADREQUEST,"Bad request, expecting AddressBookEntry")
		# create object
		entry.put()
		# return object's unique key
		return self.response_json(entry.key())
	def delete_object(self,model_name,key):
		"""Delete object by key"""
		if model_name != "AddressBookEntry":
			raise api.HTTPException(api.HTTPException.STATUS_BADREQUEST,"Bad request, expecting AddressBookEntry")
		# Retrieve object from data store
		obj = AddressBookEntry.get_by_key(long(key))
		if not obj:
			return self.response_json(False)
		# Delete the object
		obj.delete()
		# return true
		return self.response_json(True)
	def update_object(self,model_name,key,entry):
		"""Update object by key"""
		if model_name != "AddressBookEntry" or not isinstance(entry,AddressBookEntry):
			raise api.HTTPException(api.HTTPException.STATUS_BADREQUEST,"Bad request, expecting AddressBookEntry")
		# Retrieve object from data store
		obj = AddressBookEntry.get_by_key(long(key))
		if not obj:
			return self.response_json(False)
		# Update the object
		obj.update(entry)
		# return true
		return self.response_json(True)
	models = (
		AddressBookEntry,
	)
	routes = (
		(api.RequestHandler.METHOD_GET,r"^/?(\w+)/([1-9][0-9]*)$",get_object),
		(api.RequestHandler.METHOD_POST,r"^/?([\w\/]*)$",create_object),
		(api.RequestHandler.METHOD_PUT,r"^/?(\w+)/([1-9][0-9]*)$",update_object),
		(api.RequestHandler.METHOD_DELETE,r"^/?(\w+)/([1-9][0-9]*)$",delete_object)
	)
