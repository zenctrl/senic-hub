***************************
Bootstrap local development
***************************

Git Access
==========

The git repository is hosted at `GitHub <https://github.com/>`_. We have a 'master' repository located at `github.com/getsenic/nuimo-hub-app <https://github.com/getsenic/nuimo-hub-app>`_ This master repository only contains the main branches (master, staging, release etc.)

If you don't already have a GitHub account, create a new one and add your public SSH key (you won't get access via HTTP), then fork the repository to your own account, i.e. like so::

    # git clone git@github.com:getsenic/nuimo-hub-app.git
    # cd nuimo-hub-app
    # git remote add XXX -f git@github.com:XXX/nuimo-hub-app 

(where `XXX` is, of course, your username on github).

Now you are ready to set up your local development environment and join the workflow, just read on!


Requirements
============

You will need a local installation of Python 3.5, i.e. on macOS it is recommended to install a recent version of Python 3.5 using homebrew, i.e. `brew install python3.5`.

.. NOTE::
   If you don't have the Python 3.5 brew recipe locally you can "tap" it like this::

       brew tap zoidbergwill/python

   You would need to add `/usr/local/opt/python35/bin` to your PATH::

       export PATH=/usr/local/opt/python35/bin/:$PATH

With that in place, go into the `application` directory and run `make`::

    # cd application
    # make

To make sure that the installation succeeded it's a good idea to run the test suite::

    # make tests

The Makefile installed everything into a local virtualenv, so it is most convenient to activate it and then::

    # source venv/bin/activate

If all is well, you can start up a development instance of the application::

    # pserve development.ini
