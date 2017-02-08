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

download-pi3: downloads/raspbian_lite-2017-01-10/2017-01-11-raspbian-jessie-lite.zip
downloads/raspbian_lite-2017-01-10/2017-01-11-raspbian-jessie-lite.zip:
	wget -P downloads/ http://director.downloads.raspberrypi.org/raspbian_lite/images/raspbian_lite-2017-01-10/2017-01-11-raspbian-jessie-lite.zip

bootstrap: bin/ploy
	bin/ploy do $(target) bootstrap boot_ip=$(boot_ip) authorized_keys=$(authorized_keys)

osx-deps:
	brew install python openssl libffi

clean:
	git clean -fXd

.PHONY: install clean bootstrap
