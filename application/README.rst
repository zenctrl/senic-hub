Local development
=================

While the senic hub is designed to run under Linux on an embedded device most of it is just a 'normal', Python based web application and a lot of the development work and testing can be performed locally, even on non-Linux operating systems such as macos or FreeBSD (Windows not tested so far).

To install a development version of the hub locally you need two dependencies installed on your system: Python >= 3.5 and `tox`.


Install dependencies on macos
-----------------------------

Using homebrew do this::

    brew install python3
    pip install -U tox


Install dependencies on FreeBSD
-------------------------------

On FreeBSD you can do this::

    sudo pkg install python35
    sudo pip install -U pip setuptools tox


Bootstrapping the local installation
------------------------------------

With the dependencies installed, just run `make`.
This should create Python virtualenv named `venv` inside the `application` directory.
It's advisable to activate by typing `source venv/bin/activate`.


Running tests
-------------

To run the tests, just type `tox`.


Run local instance
------------------

To run a local instance of the backend, type `pserve development.ini --reload`.
You can then access the backend at `http://127.0.0.1:6543/-/`.
The `senic_hub.backend` package has been installed in development mode into the virtualenv, so any changes you make to the sources in side the `senic` folder will reflect into the running instance.
