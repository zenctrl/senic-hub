we use `LEDE <https://www.lede-project.org/>`_ as the target OS for the hub.

To build, we use a local VirtualBox instance onto which we have installed Debian/Jesse (the recommended build environment).

The provisioning of the build environment is semi-automatic (vagrant using `debian/jessie64` did not work) so we now use `ploy_virtualbox` to boot a fresh VM into the `official Debian Live CD <http://cdimage.debian.org/debian-cd/8.6.0-live/i386/iso-hybrid/>`_ where one then must use the Installer to create a fresh installation on the virtual hard disk::

  ./bin/ploy start lede-build

Then follow the installation process until the machine reboots. The resulting `.vdi` is then used as base for further configuration.

The system has been configured with users `root` and `lede` both with the password `senic<3lede`.

Vagrant
-------

after deleting the bundled `curl` (`rm /opt/vagrant/embedded/bin/curl`) vagrant works just fine :)

just do `vagrant up`...
