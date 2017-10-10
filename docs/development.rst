Developing for the hub
======================

While the backend application is written in Python and thus principally platform independent, in actuality it contains a lot of Linux- and hardware specific code that basically mandates that any development version of the stack needs to run on the hub hardware.

This section describes how to get a development board up and running so you can develop features for the hub.

To this end Senic provides special images that provide a developer-friendly environment and have been built with OpenEmbedded's debug flags enabled.

In addition, we provide some Ansible based configuration (called roles) that further customize such a development image according to your preferences (i.e. whether to perform a git checkout on the board or upload and synchronize with a local checkout of the sources).

To bootstrap a physical development board you will need to:

 - prepare a local environment

 - download a development image

 - write it to an SD card

 - boot the device from it

 - either onboard it using the setup app or access it via serial console and configure the network manually

 - apply development role(s) as required

Quick reference
---------------

Done to `Network access`

OSx
~~~

:: 

    git clone git@github.com:getsenic/senic-hub.git
    cd senic-hub/development
    make osx-deps
    make
    make download-os
    # Insert SD card into your pc
    # Change sdxxx with your card device file
    make write-osx sddev=sdXXX
    # Plug card into the hub
Ubuntu
~~~~~~


:: 

    git clone git@github.com:getsenic/senic-hub.git
    cd senic-hub/development
    make ubuntu-deps
    make
    make download-os
    # Insert SD card into your pc
    # Change sdxxx with your card device file
    make write-os-ubuntu sddev=sdXXX
    # Plug card into the hub



Preparing the local environment
-------------------------------

To apply the development role you will need a local installation of Ansible, as well as some other dependencies.
Since they are all written in Python(2) we can install them in a local virtualenv (without possibly polluting your global Python installation).

On OSX first run ``make osx-deps``, this will use homebrew to install the required system dependencies, namely, Python 2 and some development headers.

Next, run ``make`` to install the development tools locally.


Downloading the development image
---------------------------------

With all the tools in place, you next must download the development image.
This can be achieved via ``make download-os``.
This will download the main image, as well as the boot partition.


Writing the image to an SD card
-------------------------------

Currently the "burn" process is split into two parts, as the we have now working boot partition as part of the main image, so we need to 'patch' the image with a working boot partition after writing the main image.

Again, we provide a convenience target in the Makefile. To avoid accidentally deleting your harddrive, you must provide it with the name of your SD card reader explicitly, i.e. like so::

    make write-os sddev=da0

Note, that in some cases you may receive an "Invalid argument" error, however, this can be safely ignored.

Once completed, insert the card in the hub and power it up.


Network access
--------------

To develop on the board, you will first need to give it network access.
This can be either achieved using the regular setup app on your iOS or Android device or by connecting to the serial console.

To do the latter, connect via TTY (i.e. ``sudo screen /dev/tty.usbserial 115200``) and then run::

    nmcli dev wifi con <SSID> password <PASSWORD> ifname wlan0

Either way, the device should now be reachable via TCP/IP and since it's been built as a development image, you already have SSH access as ``root`` but in order to run the development playbooks you will first need to upload your own SSH public key, i.e. like so::

    scp ~/.ssh/id_rsa.pub root@192.168.1.165:/home/root/.ssh/authorized_keys

Now the device is properly reachable via SSH and you can apply the development role after updating the section `plain-instance:hub` of `senic-hub/development/etc/ploy.conf` by supplying the actual IP address that you have been assigned with::

    [plain-instance:hub]
    ....
    ip = <HUB's IP ADDRESS>

Now from `senic-hub/development` run::

    `bin/ploy configure hub`


Resetting the hub
-----------------

If we want to put the hub into delivery state, we want to stop all daemons, delete all logs and unprovision Wi-Fi (again)::

    supervisorctl stop all
    rm /srv/senic_hub/data/*
    nmcli con
    nmcli con del <CONNECTION NAME FROM PREVIOUS STEP>

Now the board can be onboarded using the app (again).

