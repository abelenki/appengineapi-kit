#!/opt/local/bin/python2.7
# encoding: utf-8

__author__ = "djt@mutablelogic.com (David Thorpe)"

# Python imports
import sys, os

# add python libraries:
#  - 'app' is for application code
#  - 'lib' for library modules
#  - 'lib3' for 3rd party modules
sys.path.append(os.path.join(os.path.dirname(__file__),'app'))
#sys.path.append(os.path.join(os.path.dirname(__file__),'lib'))
#sys.path.append(os.path.join(os.path.dirname(__file__),'lib3'))

# GAE imports
import webapp2

# app imports
from test import apihandler

# CONSTANTS
DEBUG = True

# route /api/test /api/test/ and /api/test/... messages through to the apihandler
app = webapp2.WSGIApplication([
	('/api/test',apihandler.APIHandler),
	('/api/test([\w\/]*)',apihandler.APIHandler)
],debug=DEBUG)

# add values to the registry
app.registry = {
	'debug': DEBUG
}
