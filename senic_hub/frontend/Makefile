react = node_modules/react/package.json

all: distribution/index.html

build/index.html: package.json $(react) $(shell git ls-files src/ )
	npm run build

distribution/index.html: build/index.html
	-rm -r distribution
	mv build distribution

$(react): package.json
	npm install

upload: setup.py bin/devpi distribution/index.html
	PATH=${PWD}/bin:${PATH} bin/devpi upload --no-vcs

clean:
	git clean -fXd

.PHONY: clean upload
