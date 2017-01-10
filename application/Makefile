# convenience makefile to set up the backend for local development
password = 
python_version = 3.5

all: venv/bin/pserve

tests: venv/bin/py.test
	@venv/bin/py.test

venv/bin/python$(python_version) venv/bin/pip:
	python$(python_version) -m venv venv
	venv/bin/pip install --upgrade pip

venv/bin/pserve venv/bin/py.test venv/bin/devpi: venv/bin/python$(python_version) venv/bin/pip setup.py
	venv/bin/pip install senic.cryptoyaml
	venv/bin/python$(python_version) setup.py dev
	@touch $@

upload: setup.py venv/bin/py.test venv/bin/devpi
	PATH=${PWD}/venv/bin:${PATH} venv/bin/devpi upload --no-vcs --with-docs

docs:
	$(MAKE) -C ../docs/

clean:
	git clean -fXd

.PHONY: clean tests upload
