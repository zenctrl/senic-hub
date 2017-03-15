# convenience makefile to set up the backend for local development
python_version = 3

all: venv/bin/pserve

tests: venv/bin/py.test
	@venv/bin/py.test

venv/bin/python$(python_version) venv/bin/pip venv/bin/pserve venv/bin/py.test venv/bin/devpi: 
	tox -e develop --notest

upload: setup.py venv/bin/py.test venv/bin/devpi
	PATH=${PWD}/venv/bin:${PATH} venv/bin/devpi upload --no-vcs --with-docs --formats bdist_wheel,sdist

docs:
	$(MAKE) -C ../docs/

clean:
	git clean -fXd

.PHONY: clean tests upload
