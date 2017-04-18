# convenience makefile to set up the backend for local development
python_version = 3

all: venv/bin/pserve

tests: venv/bin/py.test
	@venv/bin/py.test

venv/bin/python$(python_version) venv/bin/pip venv/bin/pserve venv/bin/py.test venv/bin/devpi: 
	tox -e develop --notest

upload: setup.py venv/bin/devpi frontend
	PATH=${PWD}/venv/bin:${PATH} venv/bin/devpi upload --no-vcs --with-docs --formats bdist_wheel,sdist

frontend:
	$(MAKE) -C senic_hub/frontend NODE_BIN=$(NODE_BIN)

docs:
	$(MAKE) -C docs/

clean:
	git clean -fXd

.PHONY: clean tests upload
