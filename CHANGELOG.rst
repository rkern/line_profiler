Changes
=======

3.0.2
~~~~~
* BUG: fix ``__version__`` attribute in Python 2 CLI.

3.0.1
~~~~~
* BUG: fix calling the package from the command line

3.0.0
~~~~~
* ENH: Fix Python 3.7
* ENH: Restructure into package

2.1
~~~
* ENH: Add support for Python 3.5 coroutines
* ENH: Documentation updates
* ENH: CI for most recent Python versions (3.5, 3.6, 3.6-dev, 3.7-dev, nightly)
* ENH: Add timer unit argument for output time granularity spec

2.0
~~~
* BUG: Added support for IPython 5.0+, removed support for IPython <=0.12

1.1
~~~
* BUG: Read source files as bytes.

1.0
~~~
* ENH: `kernprof.py` is now installed as `kernprof`.
* ENH: Python 3 support. Thanks to the long-suffering Mikhail Korobov for being
  patient.
* Dropped 2.6 as it was too annoying.
* ENH: The `stripzeros` and `add_module` options. Thanks to Erik Tollerud for
  contributing it.
* ENH: Support for IPython cell blocks. Thanks to Michael Forbes for adding
  this feature.
* ENH: Better warnings when building without Cython. Thanks to David Cournapeau
  for spotting this.

1.0b3
~~~~~

* ENH: Profile generators.
* BUG: Update for compatibility with newer versions of Cython. Thanks to Ondrej
  Certik for spotting the bug.
* BUG: Update IPython compatibility for 0.11+. Thanks to Yaroslav Halchenko and
  others for providing the updated imports.

1.0b2
~~~~~

* BUG: fixed line timing overflow on Windows.
* DOC: improved the README.

1.0b1
~~~~~

* Initial release.

