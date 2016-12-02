we use `LEDE <https://www.lede-project.org/>`_ as the target OS for the hub.

To build, we use a local VirtualBox instance onto which we have installed Debian/Jesse (the recommended build environment).

Vagrant
-------

Note: if on OSX you have trouble with bootstrapping the vagrant file, delete the bundled `curl` (`rm /opt/vagrant/embedded/bin/curl`) and vagrant works just fine :)

just do `vagrant up`...
