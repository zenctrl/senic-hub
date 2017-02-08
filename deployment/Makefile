target = pine
boot_ip = 
authorized_keys = authorized_keys
install: bin/ploy

bin/ploy bin/ploy-ssh: bin/pip requirements.txt
	bin/pip install -U pip setuptools
	bin/pip install -r requirements.txt
	@touch $@

bin/python bin/pip:
	virtualenv --python=python2.7 --clear .

download-pine64: downloads/pine64-image-ubuntubase-31065bsp-longsleep.img.xz
downloads/pine64-image-ubuntubase-31065bsp-longsleep.img.xz:
	wget -P downloads/ https://www.pine64.pro/download/ubuntu/image/pine64-image-ubuntubase-31065bsp-longsleep.img.xz 

download-pi3: downloads/ubuntu-16.04-preinstalled-server-armhf+raspi3.img.xz
downloads/ubuntu-16.04-preinstalled-server-armhf+raspi3.img.xz:
	wget -P downloads/ http://www.finnie.org/software/raspberrypi/ubuntu-rpi3/ubuntu-16.04-preinstalled-server-armhf+raspi3.img.xz

bootstrap: bin/ploy
	bin/ploy do $(target) bootstrap boot_ip=$(boot_ip) authorized_keys=$(authorized_keys)

osx-deps:
	brew install python openssl libffi

clean:
	git clean -fXd

.PHONY: install clean bootstrap
