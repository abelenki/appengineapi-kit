#!/opt/local/bin/python2.7
# encoding: utf-8

__author__ = "djt@mutablelogic.com (David Thorpe)"

# Python imports
import logging

# Imports from appengineapi-kit
from appengineapi_kit import api,model,gaedatastore

class AddressBookEntry(model.Model):
	# STORAGE
	proxy = gaedatastore.DataStore("addressbook_entry")
	# PROPERTIES
	name = model.StringProperty(notnull=True,minlength=0,maxlength=100)
	email = model.StringProperty(notnull=False,minlength=0,maxlength=100)

class RequestHandler(api.RequestHandler):
	"""Implementation of the Address Book API"""
	def _get_param_limit(self):
		limit = self.request.get('limit',None)
		if limit==None or len(limit)==0:
			return None
		try:
			limit = long(limit)
			if limit <= 0:
				raise ValueError()
			return limit
		except ValueError, e:
			raise api.HTTPException(api.HTTPException.STATUS_BADREQUEST,"Invalid 'limit' parameter")
	def get_object(self,name,key):
		"""Get AddressBookEntry object"""
		if name != "addressbook_entry":
			raise api.HTTPException(api.HTTPException.STATUS_BADREQUEST,"Bad request, expecting addressbook_entry")
		entry = AddressBookEntry.get_by_key(long(key))
		if not entry:
			raise api.HTTPException(api.HTTPException.STATUS_NOTFOUND,"No addressbook_entry entity with key %s" % key)
		assert isinstance(entry,AddressBookEntry)
		return self.response_json(entry)
	def get_feed(self,name):
		"""Get AddressBookEntry feed"""
		if name != "addressbook_entry":
			raise api.HTTPException(api.HTTPException.STATUS_BADREQUEST,"Bad request, expecting addressbook_entry")
		query = AddressBookEntry.get_query()
		limit = self._get_param_limit()
		return self.response_json(query.execute(limit=limit))
	def create_object(self,path,entry):
		"""Create new AddressBookEntry object"""
		if not isinstance(entry,AddressBookEntry):
			raise api.HTTPException(api.HTTPException.STATUS_BADREQUEST,"Bad request, expecting addressbook_entry")
		# create object
		entry.put()
		# return entity
		return self.response_json(entry)
	def delete_object(self,name,key):
		"""Delete object by key"""
		if name != "addressbook_entry":
			raise api.HTTPException(api.HTTPException.STATUS_BADREQUEST,"Bad request, expecting addressbook_entry")
		# Retrieve object from data store
		obj = AddressBookEntry.get_by_key(long(key))
		if not obj:
			raise api.HTTPException(api.HTTPException.STATUS_NOTFOUND,"No addressbook_entry entity with key %s" % key)
		# Delete the object
		obj.delete()
		# return true
		return self.response_json(True)
	def update_object(self,name,key,entry):
		"""Update object by key"""
		if name != "addressbook_entry" or (not isinstance(entry,AddressBookEntry) and not isinstance(entry,dict)):
			raise api.HTTPException(api.HTTPException.STATUS_BADREQUEST,"Bad request, expecting addressbook_entry")
		# Retrieve object from data store
		obj = AddressBookEntry.get_by_key(long(key))
		if not obj:
			raise api.HTTPException(api.HTTPException.STATUS_NOTFOUND,"No addressbook_entry entity with key %s" % key)
		# Update the object, put back
		try:
			obj.update(entry)
		except TypeError, e:
			raise api.HTTPException(api.HTTPException.STATUS_BADREQUEST,"Bad request: %s" % e)
		# return true
		return self.response_json(obj)
	models = (
		AddressBookEntry,
	)
	routes = (
		(api.RequestHandler.METHOD_GET,r"^/?(\w+)/([1-9][0-9]*)$",get_object),
		(api.RequestHandler.METHOD_GET,r"^/?(\w+)$",get_feed),
		(api.RequestHandler.METHOD_POST,r"^/?([\w\/]*)$",create_object),
		(api.RequestHandler.METHOD_PUT,r"^/?(\w+)/([1-9][0-9]*)$",update_object),
		(api.RequestHandler.METHOD_DELETE,r"^/?(\w+)/([1-9][0-9]*)$",delete_object)
	)
