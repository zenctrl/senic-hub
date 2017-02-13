Provisioning and configuring the hub
------------------------------------

On OSX first run ``make osx-deps``, this will use homebrew to install the required system dependencies, namely, Python 3 and some development headers.

Next, run ``make`` to install the development tools locally.

For development and testing we provision either a RasperberryPI3, PINE64, NanoPI Neo Air or a vagrant based Virtualbox instance using an ubuntu base image that we then customize using ansible.

Bootstrapping vagrant
=====================

Assuming fairly recent installations of vagrant and Virtualbox, you can simply run `vagrant up hub` and it will download the required base image and bootstrap it automatically.


Bootstrapping a development board
=================================

To bootstrap a physical development board you will need to

- download the appropriate base image

- write it to an SD card

- boot the device from it

- figure out the IP address that the device has been given

- bootstrap the device using that IP address (at the end of which it will have the 'real' IP address that it has been configured to have - this way we can have known IP addresses for configuration)

To download the base image use `make download-XXX` where `XXX` is one of `pi3`, `nanopi` or `pine64`.

Then write the image to an SD card using your tool of choice (https://etcher.io/ seems like a fluffy choice for OSX) and boot the board, making sure you have a working DHCP setup.

The first step is to bootstrap the booted board into a state where we can configure it via ansible.
This is done using a helper tool called `ploy` which is a modular configuration system that (in this case) combines `ansible <http://docs.ansible.com/ansible/>`_ and `fabric <http://www.fabfile.org/>`_.
The `Makefile` installs a local instance of `ploy` and its dependencies by default, so you should run `make` first.

After booting the device you need to figure out the IP address it has been given.

Next, create an entry in `etc/ploy.conf` using one of the existing entries as an example.

Then run `make bootstrap target=XXX` where `XXX` is the name you have given in the configuration file.

If you don't want to use the IP address given via DHCP you can set the desired IP in the configuration and pass the current IP address via the `boot_ip` parameter like so::

    make bootstrap target=XXX boot_ip=192.168.1.39

After a minute or two, the board should reboot and is now ready for action.


Bootstrapping the RasperberryPI3
********************************

The default login is `ubuntu/ubuntu` but you are forced to change the password immediately. You must follow this procedure either via SSH or via keyboard/monitor before you can perform the Bootstrapping.

Then, during bootstrapping you will be asked (once) for the password you set and from then on you can log in using the SSH key you configured.