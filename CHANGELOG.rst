Changes
=======

3.3.0
~~~~~
* New CI for building wheels.

3.2.6
~~~~~
* FIX: Update MANIFEST.in to package pyproj.toml and missing pyx file
* CHANGE: Removed version experimental augmentation. 

3.2.5
~~~~~
* FIX: Update MANIFEST.in to package nested c source files in the sdist

3.2.4
~~~~~
* FIX: Update MANIFEST.in to package nested CMakeLists.txt in the sdist

3.2.3
~~~~~
* FIX: Use ImportError instead of ModuleNotFoundError while 3.5 is being supported
* FIX: Add MANIFEST.in to package CMakeLists.txt in the sdist

3.2.2
~~~~~
* ENH: Added better error message when c-extension is not compiled.
* FIX: Kernprof no longer imports line_profiler to avoid side effects.

3.2.0
~~~~~
* Dropped 2.7 support, manylinux docker images no longer support 2.7 
* ENH: Add command line option to specify time unit and skip displaying
  functions which have not been profiled.
* ENH: Unified versions of line_profiler and kernprof: kernprof version is now
  identical to line_profiler version.

3.1.0
~~~~~
* ENH: fix Python 3.9

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

