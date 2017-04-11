NODE_BIN = dirname `which node`
react = node_modules/react/package.json

all: distribution/index.html

build/index.html: package.json $(react) $(shell git ls-files src/ )
	PATH=${NODE_BIN}:${PATH} npm run build

distribution/index.html: build/index.html
	-rm -r distribution
	mv build distribution

$(react): package.json
	PATH=${NODE_BIN}:${PATH} npm install

clean:
	git clean -fX

.PHONY: clean
