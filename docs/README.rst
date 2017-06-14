The Senic Hub
-------------

The Senic Hub is a **Bluetooth Low Energy and Wi-Fi-enabled smart home hub** that allows a user to connect to their smart devices (such as Sonos, Philips Hue etc).
It also works together with the `Senic Nuimo <https://www.senic.com/en/nuimo>`_, our very own bluetooth controller for smart devices and significantly extends its usefulness by eliminating the need to having it connected to a smart phone or tablet.

This repository contains the entire software stack that we created for the hub.

While it is divided into several separate modules that run in independent processes we have chosen to keep them not only in a common repository but also to package them as a single python package because in the end all of these components need to work together and oftentimes features are spread across several modules.
This allows for simpler versioning (there is only one canonical version) and also makes it easier to create pull requests.

The hub is divided into the following modules:

- The (RESTful) **backend** – a `pyramid <http://docs.pylonsproject.org/projects/pyramid/en/latest/>`_ application that clients talk to via HTTP
- The **Nuimo application** – the entity that the *nuimo controller* talks to via bluetooth
- **bluenetd** – a process that implements a bluetooth hub for clients to connect to during onboarding
- **setup_app** – a cross-platform, react native app that runs on iOS and Android and which talks bluetooth and HTTP with the bluenetd and the backend to setup and configure the hub
- Additionally the hub also consists of an instance of `homeassistant <https://home-assistant.io/>`_ but since that is an unmodified instance of the latest supported version its sources are not part of this repository

All of these components are controlled using supervisord.
