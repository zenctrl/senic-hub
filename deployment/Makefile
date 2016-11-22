install: bin/ploy

bin/ploy bin/ploy-ssh: bin/pip requirements.txt
	bin/pip install -r requirements.txt
	@touch $@

bin/python bin/pip:
	virtualenv --python=python2.7 --clear .

download-base: downloads/pine64-image-ubuntubase-31065bsp-longsleep.img.xz
downloads/pine64-image-ubuntubase-31065bsp-longsleep.img.xz:
	wget -P downloads/ https://www.pine64.pro/download/ubuntu/image/pine64-image-ubuntubase-31065bsp-longsleep.img.xz 

clean:
	git clean -fXd

.PHONY: install clean 
