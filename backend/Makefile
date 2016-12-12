# convenience makefile to set up the backend for local development
password = 

all: venv/bin/pserve

tests: venv/bin/py.test
	@venv/bin/py.test

venv/bin/python venv/bin/pip:
	python3.5 -m venv venv
	venv/bin/pip install --upgrade pip

venv/bin/pserve venv/bin/py.test venv/bin/devpi: venv/bin/python venv/bin/pip setup.py
	venv/bin/python setup.py dev
	@touch $@

upload: setup.py venv/bin/py.test venv/bin/devpi
	PATH=${PWD}/venv/bin:${PATH} venv/bin/devpi upload --no-vcs

initdb: name = $(shell venv/bin/python setup.py --name)
initdb: venv/bin/python venv/bin/alembic
	@psql -c "" $(name) 2> /dev/null || createdb $(name) -E utf8 -T template0
	venv/bin/alembic upgrade head

docs:
	$(MAKE) -C docs/

clean:
	git clean -fXd

.PHONY: initdb clean tests upload
