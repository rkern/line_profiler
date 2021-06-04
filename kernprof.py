#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" Script to conveniently run profilers on code in a variety of circumstances.
"""

import functools
import os
import sys
from argparse import ArgumentError, ArgumentParser

# NOTE: This version needs to be manually maintained with the line_profiler
# __version__ for now.
__version__ = '3.3.0'

PY3 = sys.version_info[0] == 3

# Guard the import of cProfile such that 3.x people
# without lsprof can still use this script.
try:
    from cProfile import Profile
except ImportError:
    try:
        from lsprof import Profile
    except ImportError:
        from profile import Profile


# Python 3.x compatibility utils: execfile
# ========================================
try:
    execfile
except NameError:
    # Python 3.x doesn't have 'execfile' builtin
    import builtins
    exec_ = getattr(builtins, "exec")

    def execfile(filename, globals=None, locals=None):
        with open(filename, 'rb') as f:
            exec_(compile(f.read(), filename, 'exec'), globals, locals)
# =====================================



CO_GENERATOR = 0x0020
def is_generator(f):
    """ Return True if a function is a generator.
    """
    isgen = (f.__code__.co_flags & CO_GENERATOR) != 0
    return isgen


class ContextualProfile(Profile):
    """ A subclass of Profile that adds a context manager for Python
    2.5 with: statements and a decorator.
    """

    def __init__(self, *args, **kwds):
        super(ContextualProfile, self).__init__(*args, **kwds)
        self.enable_count = 0

    def enable_by_count(self, subcalls=True, builtins=True):
        """ Enable the profiler if it hasn't been enabled before.
        """
        if self.enable_count == 0:
            self.enable(subcalls=subcalls, builtins=builtins)
        self.enable_count += 1

    def disable_by_count(self):
        """ Disable the profiler if the number of disable requests matches the
        number of enable requests.
        """
        if self.enable_count > 0:
            self.enable_count -= 1
            if self.enable_count == 0:
                self.disable()

    def __call__(self, func):
        """ Decorate a function to start the profiler on function entry and stop
        it on function exit.
        """
        # FIXME: refactor this into a utility function so that both it and
        # line_profiler can use it.
        if is_generator(func):
            wrapper = self.wrap_generator(func)
        else:
            wrapper = self.wrap_function(func)
        return wrapper

    # FIXME: refactor this stuff so that both LineProfiler and
    # ContextualProfile can use the same implementation.
    def wrap_generator(self, func):
        """ Wrap a generator to profile it.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwds):
            g = func(*args, **kwds)
            # The first iterate will not be a .send()
            self.enable_by_count()
            try:
                item = next(g)
            except StopIteration:
                return
            finally:
                self.disable_by_count()
            input = (yield item)
            # But any following one might be.
            while True:
                self.enable_by_count()
                try:
                    item = g.send(input)
                except StopIteration:
                    return
                finally:
                    self.disable_by_count()
                input = (yield item)
        return wrapper

    def wrap_function(self, func):
        """ Wrap a function to profile it.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwds):
            self.enable_by_count()
            try:
                result = func(*args, **kwds)
            finally:
                self.disable_by_count()
            return result
        return wrapper

    def __enter__(self):
        self.enable_by_count()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disable_by_count()


def find_script(script_name):
    """ Find the script.

    If the input is not a file, then $PATH will be searched.
    """
    if os.path.isfile(script_name):
        return script_name
    path = os.getenv('PATH', os.defpath).split(os.pathsep)
    for dir in path:
        if dir == '':
            continue
        fn = os.path.join(dir, script_name)
        if os.path.isfile(fn):
            return fn

    sys.stderr.write('Could not find script %s\n' % script_name)
    raise SystemExit(1)


def main(args=None):
    def positive_float(value):
        val = float(value)
        if val <= 0:
            raise ArgumentError
        return val

    parser = ArgumentParser(description="Run and profile a python script.")
    parser.add_argument('-V', '--version', action='version', version=__version__)
    parser.add_argument('-l', '--line-by-line', action='store_true',
        help="Use the line-by-line profiler instead of cProfile. Implies --builtin.")
    parser.add_argument('-b', '--builtin', action='store_true',
        help="Put 'profile' in the builtins. Use 'profile.enable()'/'.disable()', "
            "'@profile' to decorate functions, or 'with profile:' to profile a "
            "section of code.")
    parser.add_argument('-o', '--outfile',
        help="Save stats to <outfile> (default: 'scriptname.lprof' with "
            "--line-by-line, 'scriptname.prof' without)")
    parser.add_argument('-s', '--setup',
        help="Code to execute before the code to profile")
    parser.add_argument('-v', '--view', action='store_true',
        help="View the results of the profile in addition to saving it")
    parser.add_argument('-u', '--unit', default='1e-6', type=positive_float,

        help="Output unit (in seconds) in which the timing info is "
        "displayed (default: 1e-6)")
    parser.add_argument('-z', '--skip-zero', action='store_true',
        help="Hide functions which have not been called")

    parser.add_argument('script', help="The python script file to run")
    parser.add_argument('args', nargs='...', help="Optional script arguments")

    options = parser.parse_args(args)

    if not options.outfile:
        extension = 'lprof' if options.line_by_line else 'prof'
        options.outfile = '%s.%s' % (os.path.basename(options.script), extension)


    sys.argv = [options.script] + options.args
    if options.setup is not None:
        # Run some setup code outside of the profiler. This is good for large
        # imports.
        setup_file = find_script(options.setup)
        __file__ = setup_file
        __name__ = '__main__'
        # Make sure the script's directory is on sys.path instead of just
        # kernprof.py's.
        sys.path.insert(0, os.path.dirname(setup_file))
        ns = locals()
        execfile(setup_file, ns, ns)

    if options.line_by_line:
        import line_profiler
        prof = line_profiler.LineProfiler()
        options.builtin = True
    else:
        prof = ContextualProfile()
    if options.builtin:
        if PY3:
            import builtins
        else:
            import __builtin__ as builtins
        builtins.__dict__['profile'] = prof

    script_file = find_script(options.script)
    __file__ = script_file
    __name__ = '__main__'
    # Make sure the script's directory is on sys.path instead of just
    # kernprof.py's.
    sys.path.insert(0, os.path.dirname(script_file))

    try:
        try:
            execfile_ = execfile
            ns = locals()
            if options.builtin:
                execfile(script_file, ns, ns)
            else:
                prof.runctx('execfile_(%r, globals())' % (script_file,), ns, ns)
        except (KeyboardInterrupt, SystemExit):
            pass
    finally:
        prof.dump_stats(options.outfile)
        print('Wrote profile results to %s' % options.outfile)
        if options.view:
            if isinstance(prof, ContextualProfile):
                prof.print_stats()
            else:
                prof.print_stats(output_unit=options.unit,
                                 stripzeros=options.skip_zero)


if __name__ == '__main__':
    main(sys.argv[1:])
