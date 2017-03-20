react = node_modules/react/package.json

all: distribution/index.html bin/devpi

build/index.html: package.json $(react) $(shell git ls-files src/ )
	npm run build

distribution/index.html: build/index.html
	mv build distribution

$(react): package.json
	npm install

bin/devpi: bin/python bin/pip
	bin/pip install --upgrade setuptools pip
	bin/pip install devpi-client
	@touch $@

bin/python bin/pip:
	python3 -m venv .

upload: setup.py bin/devpi distribution/index.html
	PATH=${PWD}/bin:${PATH} bin/devpi upload --no-vcs

clean:
	git clean -fXd

.PHONY: clean upload
