appengineapi-kit
================

Introduction
------------

This is the beginning of a tutorial on using Google App Engine to 
create an API interface in Python. By "API" I mean a framework which
allows you to retrieve data from a data store source, manipulate it,
update, create and delete it. This tutorial will be split into the
following parts:

  1. The App Engine framework
  2. Routing API calls
  3. Data model and data design
  4. Creating, updating and deleting data
  5. Using AngularJS to build a web application
  6. Authentication and authorization for API calls
  7. Using Google's Cloud SQL service

The App Engine Framework
------------------------

The first step to build the application is to make a framework around
Google App Engine. You can switch to the 'step1' branch to demonstrate this
here:

```
git checkout -b step1
```

This will create a `appengineapi-kit` folder which includes the following
structure:

  * The `app.yaml` file  describes the Google App Engine application
  * The `application.py` file sets up the application, and routes requests
    through to the various request handlers.
  * The `dev_appserver.sh` starts and stops the App Engine development 
    environment
  * The `app` folder contains application code
  * The `lib` folder will contain re-usable library code
  * The `lib3` folder will contain 3rd party library code
  * The `doc` folder contains documentation and examples
  * The `static` folder will contain any statically served files
  * The `templates` folder will contain HTML templates

Once you've installed the Google App Engine runtime, you can start the
development webserver using the following command:

```
   cd appengineapi-kit
   ./dev_appserver.sh
```

You should then be able to make requests to return data:

```
  curl -X GET http://localhost:8080/api/test
```

This command routes the request through to `test.apihandler.RequestHandler` which is a subclass of 
`webapp2.webapp2.RequestHandler`. It simply takes the path argument and responds using a JSON
response, which is something that JavaScript (and other languages) can take back in and process
again. So for example:

```
   curl -X GET http://localhost:8080/api/test
   => []

   curl -X GET http://localhost:8080/api/test/
   => ["/"]

   curl -X GET http://localhost:8080/api/test/fetch
   => [ "/fetch" ]
```

Routing API calls
-----------------

The second step to build the application is to route API calls from a remote
web client to class methods within our `RequestHandler` object. You can switch
to the 'step2' branch to demonstrate this here:

```
git checkout -b step2
```

In this step, the following files are added and/or modified:

  * The `lib` folder contains a module `appengineapi_kit.api` which
    defines a general way to deal with API calls
  * The `test` folder has an updated `apihandler.RequestHandler` which
    inherits from `appengineapi_kit.api.RequestHandler`

The `apihandler.RequestHandler` has a number of methods which are used to
implement the general request and response cycle for each API call:

  * The `get`,`post`,`delete` and `put` methods simply route the request
    through to a general `route_request` method, which pattern matches
    against your pre-defined API call routes.
  * The `route_request` method will match the method of the API request
    and the pre-defined patterns to call specific API handling routines.
  * The `response_json` method can be used to respond back to the client
    with a JSON message. For errors, the HTTP status code is set to an
    appropriate error response code.

Errors are caught when a `appengineapi_kit.api.HTTPException` object
is raised. In this case, a JSON response is also sent. If you raise other
exceptions, they will not return a JSON response to the client, so
it's important to catch errors within your own `RequestHandler` classes
and re-raise as `HTTPException` objects.

Here is how the updated `apihandler.RequestHandler` class now looks:

```python
class RequestHandler(api.RequestHandler):
	def get_object(self,*path):
		return self.response_json(path)
	routes = (
		(api.RequestHandler.METHOD_GET,r"^/?([\w\/]*)$",get_object),
	)
```

The potential API calls are defined in the `routes` property of the
class. This is a series of tuple values in triplets. The first value
is one of the following values:

  * `api.RequestHandler.METHOD_GET` where the API call is retrieving
    data
  * `api.RequestHandler.METHOD_POST` where the API call is creating
    data
  * `api.RequestHandler.METHOD_PUT` where the API call is updating
    data
  * `api.RequestHandler.METHOD_DELETE` where the API call is deleting
    data

The second value in each tuple is the regular expression to use when
matching the path. If no pattern is found by the `route_request` method,
then a 404 HTTP status message is returned to the client. If you use
groups within the regular expression, these are passed as arguments
to your method.

The third value in each tuple is a reference to the method to call
when the pattern is matched. In the example here, the `get_object`
method accepts a variable number of arguments and sends a JSON
response of the path arguments back to the client. Here are some
examples of how this might work:

```
   curl -X GET http://localhost:8080/api/test
   => [""]

   curl -X GET http://localhost:8080/api/test/
   => [""]

   curl -X GET http://localhost:8080/api/test/fetch
   => [ "fetch" ]

   curl -X GET http://localhost:8080/api/testfetch
   => [ "fetch" ]
```

Data model and data design
--------------------------
The third step to build the application is to store some data on the server
when it's passed through from the client. You can switch to the 'step3' 
branch to demonstrate this here:

```
git checkout -b step3
```

In this step, the following files are added and/or modified:

  * The `appengineapi_kit.api` module contains Model and
    ModelProperty classes.
  * The `test` folder has an updated `apihandler.RequestHandler` which
    defines the models which are allowable instances for API requests
    and responses.

By defining classes which inherit from `api.Model`, your code can
create clean interfaces to communicate to and from external clients.
Here is an example 'AddressBookEntry' model which could be used to
communicate:

```python
class AddressBookEntry(api.Model):
	# MODEL NAME
	model_name = "AddressBookEntry"
	# PROPERTIES
	name = api.StringProperty(notnull=True,minlength=0,maxlength=100)
	email = api.StringProperty(notnull=False,minlength=0,maxlength=100)
```

Here the `model_name` property defines the unique name for the interface,
and the members of the model class are defined as `name` and `email`. Some
additional parameters are used to limit the values that the members can
contain.

The request handler `test.RequestHandler` then defines the models which
will be accepted from clients. For example,

```python
class RequestHandler(api.RequestHandler):
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
```

Here, there is a single route which returns an `AddressBookEntry` object regardless.
This is now what happens when communicating with the server:

```
   curl -X GET http://localhost:8080/api/test
   => {'_type': 'AddressBookEntry', 'email': 'fred@bloggs.com', 'name': 'Fred Bloggs'}
```

The method `api.RequestHandler.response_json` returns this response by:

  * Checking if the response should be a `api.HTTPException` response, or,
  * Checking if the response should be a `dict`, `string`, `bool` or `int`, or,
  * Checking if the response should be an `api.Model`.

In the third case, the `api.Model.as_json` method is used to decode the model object
into a json response. As well as the model properties, the `_type` property is used
to return the `model_name` property.



