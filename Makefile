all:
	@echo 'Just some tools to help me make releases. Nothing for users.'

index.html: README.rst
	rst2html.py README.rst index.html

pypi-site-docs.zip: index.html kernprof.py LICENSE.txt
	zip -r $@ $?

site: pypi-site-docs.zip

# We need to run build_ext first to make sure we have _line_profiler.c.
# However, we can't run both commands in the same run.
sdist:
	python setup.py build_ext
	python setup.py sdist

.PHONY: site sdist
