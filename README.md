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

Proceed to this branch where the README.md file contains the next steps.
