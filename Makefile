all:
	@echo 'Just some tools to help me make releases. Nothing for users.'

index.html: README.txt
	rst2html.py README.txt index.html

pypi-site-docs.zip: index.html kernprof.py LICENSE.txt
	zip -r $@ $?

site: pypi-site-docs.zip

.PHONY: site
