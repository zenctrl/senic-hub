***************************
Bootstrap local development
***************************

Git Access
----------

The git repository is hosted at `GitHub <https://github.com/>`_. We have a 'master' repository located at `github.com/getsenic/senic-hub <https://github.com/getsenic/senic-hub>`_ This master repository only contains the main branches (master, staging, release etc.)

If you don't already have a GitHub account, create a new one and add your public SSH key (you won't get access via HTTP), then fork the repository to your own account, i.e. like so::

    # git clone git@github.com:getsenic/senic-hub.git
    # cd senic-hub
    # git remote add XXX -f git@github.com:XXX/senic-hub 

(where `XXX` is, of course, your username on github).

Now you are ready to set up your local development environment and join the workflow, just read on!

While the senic hub is designed to run under Linux on an embedded device most of it is just a 'normal', Python based web application and a lot of the development work and testing can be performed locally, even on non-Linux operating systems such as macos or FreeBSD (Windows not tested so far).

To install a development version of the hub locally you need two dependencies installed on your system: Python >= 3.5 and `tox`.


Install dependencies on macos
-----------------------------

Using homebrew do this::

    brew install python3
    pip3 install -U tox


Install dependencies on FreeBSD
-------------------------------

On FreeBSD you can do this::

    sudo pkg install python35
    sudo pip install -U pip setuptools tox


Bootstrapping the local installation
------------------------------------

With the dependencies installed, just run `make`.
This should create Python virtualenv named `venv` inside the `application` directory.
It's advisable to activate it by typing `source venv/bin/activate`.


Running tests
-------------

To run the tests, just type `tox`.

To run tests during development without packaging and coverage checks you can speed up test execution by running:

1. `make` # Only necessary once
2. `venv/bin/activate`
3. `py.test` # Use `py.test -k <regex>` to run tests only from specific test suite or specific test methods


Run local instance
------------------

To run a local instance of the backend, type `pserve development.ini --reload`.
You can then access the backend at `http://127.0.0.1:6543/-/`.
The `senic_hub.backend` package has been installed in development mode into the virtualenv, so any changes you make to the sources in side the `senic` folder will reflect into the running instance.
