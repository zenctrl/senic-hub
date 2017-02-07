Provisioning and configuring the hub
------------------------------------

On OSX first run ``make osx-deps``, this will use homebrew to install the required system dependencies, namely, Python 3 and some development headers.

Next, run ``make`` to install the development tools locally.

For development and testing we provision a PINE64 board using an ubuntu base image that we then customize using ansible.

To download the base image use `make download-base`.

Then write the image to an SD card using your tool of choice (https://etcher.io/ seems like a fluffy choice for OSX) and boot the board, making sure you have a working DHCP setup.

The first step is to bootstrap the booted board into a state where we can configure it via ansible.
This is done using a helper tool called `ploy` which is a modular configuration system that (in this case) combines `ansible <http://docs.ansible.com/ansible/>`_ and `fabric <http://www.fabfile.org/>`_.
The `Makefile` installs a local instance of `ploy` and its dependencies by default, so you should run `make` first.

For example, you can use OSX's 'Internet Sharing' feature to i.e. share the wifi connection over ethernet and connect the board directly via ethernet.
This has the added advantage that the board has no direct access to the rest of your network (and vice versa). In this case the board will receive an IP address of `192.168.2.1`` by default, which is also the default value configured in `etc/ploy.conf`.

Otherwise, log into the device directly (i.e. with keyboard and display) using the default `ubuntu/ubuntu` credentials, issue `ifconfig eth0` and note the IP address given via DHCP and pass that into the bootstrap command like so::

    make bootstrap boot_ip=192.168.1.39

Then you can run `make bootstrap` and watch the show... After a minute or two, the board should reboot and is now ready for action.
