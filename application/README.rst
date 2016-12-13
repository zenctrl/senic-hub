Setting up a local development environment
==========================================

Requirements
------------

Local packages that need to be installed:

 - Python3.5

 - Postgresql 9.x


Bootstrap
---------

You now can simply run `make` to install all development requirements

Either way, to check that everything is working, you should run the test suite once, like so::

    make tests

Note, if you get an error like::

    sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) FATAL:  role "XXX" does not exist

where `XXX` is your username, you must give yourself the privilege to create a postgresql database like so::

    createuser -d XXX