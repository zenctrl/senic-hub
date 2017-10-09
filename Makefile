# convenience makefile to generate the documentation and upload releases
# it requires a global installation of tox
python_version = 3

venv/bin/python$(python_version) venv/bin/pip venv/bin/pserve venv/bin/py.test venv/bin/devpi: 
	tox -e develop --notest

upload: setup.py venv/bin/devpi
	PATH=${PWD}/venv/bin:${PATH} venv/bin/devpi upload --no-vcs --with-docs --formats bdist_wheel,sdist

docs:
	$(MAKE) -C docs/

clean:
	git clean -fXd

.PHONY: clean upload
