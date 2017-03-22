.. _index:

***************
:mod:`senic_hub
***************

:Author: Senic GmbH
:Version: |version|

.. module:: senic_hub

Overview
========

The *senic_hub* appliation is the RESTful backend running on the nuimo hub device. It sits between clients (mainly a web frontend) and the low-level drivers that manage the actual connection to the nuimo devices.

Its main purpose is to provide a bootstrapping experience when users set up the hub for the first time, to connect and manage nuimos and integrations.

It is designed as a client/server application. The server (this project) is written in Python using the `Pyramid framework <http://docs.pylonsproject.org/projects/pyramid/en/1.7-branch/>`_ and (mostly) serves and processes JSON data.


Development
===========

Start here if you want to develop the hub application.

.. toctree::
    :maxdepth: 3

    bootstrap-dev
    vagrant
