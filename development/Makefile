target = pi3hub
boot_ip =
authorized_keys = authorized_keys
configure_ethernet = yes

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

clean:
	git clean -fXd

.PHONY: install clean
