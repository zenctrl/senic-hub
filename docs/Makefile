# convenience makefile to set up the project documentation

bin = ../backend/venv/bin

htdocs: $(bin)/sphinx-build *.rst conf.py
	$(bin)/sphinx-build . $@

$(bin)/sphinx-build:
	$(MAKE) -C ../

clean:
	git clean -fXd

.PHONY: clean htdocs
