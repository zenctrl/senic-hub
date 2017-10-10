sddev=XXX

install: bin/ploy etc/ploy.conf

bin/ploy bin/ploy-ssh: bin/pip requirements.txt
	bin/pip install -U pip setuptools
	bin/pip install -r requirements.txt
	@touch $@

bin/python bin/pip:
	virtualenv --system-site-packages --python=python2.7 --clear .

etc/ploy.conf:
	cp etc/ploy.conf.sample etc/ploy.conf

osx-deps:
	brew install python openssl libffi


ubuntu-deps:
	sudo apt-get install virtualenv python-dev

# downloading and writing a development image
downloads:
	mkdir -p downloads

download-os: downloads
	wget -c --show-progress https://bob.senic.com/senic-os/releases/senic-os-dev-senic-hub-beta.sdimg -o downloads/senic-os-dev-senic-hub-beta.sdimg
	wget -c https://bob.senic.com/senic-os/releases/u-boot-sunxi-with-spl.bin -o downloads/u-boot-sunxi-with-spl.bin

write-os:
	# first write the sdimg:
	sudo dd bs=2m of=/dev/$(sddev) if=downloads/senic-os-dev-senic-hub-beta.sdimg
	# then write the boot partition (you can ignore errors re: "invalid argument")
	-sudo dd bs=1024 of=/dev/$(sddev) seek=8 if=downloads/u-boot-sunxi-with-spl.bin

write-os-ubuntu:
	-sudo umount /dev/$(sddev)*
	# first write the sdimg:
	sudo dd bs=2M of=/dev/$(sddev) if=senic-os/$(oshost)/$(osuser)/$(osenv)/senic-os-dev-senic-hub-beta.sdimg status=progress
	# then write the boot partition (you can ignore errors re: "invalid argument")
	sleep 1
	-sudo umount /dev/$(sddev)*
	sudo dd bs=1024 of=/dev/$(sddev) seek=8 if=senic-os/$(oshost)/$(osuser)/$(osenv)/u-boot-sunxi-with-spl.bin status=progress
	-sudo umount /dev/$(sddev)*


write-osx:
	# make sure the disk is not mounted
	-diskutil unmountDisk /dev/$(sddev)
	# first write the sdimg:
	sudo dd bs=2m of=/dev/$(sddev) if=senic-os/$(oshost)/$(osuser)/$(osenv)/senic-os-dev-senic-hub-beta.sdimg
	diskutil unmountDisk /dev/$(sddev)
	# then write the boot partition (you can ignore errors re: "invalid argument")
	-sudo dd bs=1024 of=/dev/$(sddev) seek=8 if=senic-os/$(oshost)/$(osuser)/$(osenv)/u-boot-sunxi-with-spl.bin
	-diskutil unmountDisk /dev/$(sddev)

clean:
	git clean -fXd

.PHONY: install clean download-os
