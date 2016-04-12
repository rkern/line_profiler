#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
import functools
import inspect
import linecache
import locale
import argparse
import os
import re
import sys

from _line_profiler import LineProfiler as CLineProfiler

_version = "1.0b2"

# For locale.format number grouping (option --grouped-numbers)
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

# Python 2/3 compatibility utils
# ===========================================================
PY3 = sys.version_info[0] == 3

# exec (from https://bitbucket.org/gutworth/six/):
if PY3:
    import builtins
    exec_ = getattr(builtins, "exec")
    del builtins
else:
    def exec_(_code_, _globs_=None, _locs_=None):
        """Execute code in a namespace."""
        if _globs_ is None:
            frame = sys._getframe(1)
            _globs_ = frame.f_globals
            if _locs_ is None:
                _locs_ = frame.f_locals
            del frame
        elif _locs_ is None:
            _locs_ = _globs_
        exec("""exec _code_ in _globs_, _locs_""")

# ============================================================

CO_GENERATOR = 0x0020
def is_generator(f):
    """ Return True if a function is a generator.
    """
    isgen = (f.__code__.co_flags & CO_GENERATOR) != 0
    return isgen


class LineProfiler(CLineProfiler):
    """ A profiler that records the execution times of individual lines.
    """

    def __call__(self, func):
        """ Decorate a function to start the profiler on function entry and stop
        it on function exit.
        """
        self.add_function(func)
        if is_generator(func):
            wrapper = self.wrap_generator(func)
        else:
            wrapper = self.wrap_function(func)
        return wrapper

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
            finally:
                self.disable_by_count()
            input = (yield item)
            # But any following one might be.
            while True:
                self.enable_by_count()
                try:
                    item = g.send(input)
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

    def dump_stats(self, filename):
        """ Dump a representation of the data to a file as a pickled LineStats
        object from `get_stats()`.
        """
        lstats = self.get_stats()
        with open(filename, 'wb') as f:
            pickle.dump(lstats, f, pickle.HIGHEST_PROTOCOL)

    def print_stats(self, stream=None, stripzeros=False, options=None):
        """ Show the gathered statistics.
        """
        lstats = self.get_stats()
        show_text(lstats.timings, lstats.unit, stream=stream, stripzeros=stripzeros, options=options)

    def run(self, cmd):
        """ Profile a single executable statment in the main namespace.
        """
        import __main__
        main_dict = __main__.__dict__
        return self.runctx(cmd, main_dict, main_dict)

    def runctx(self, cmd, globals, locals):
        """ Profile a single executable statement in the given namespaces.
        """
        self.enable_by_count()
        try:
            exec_(cmd, globals, locals)
        finally:
            self.disable_by_count()
        return self

    def runcall(self, func, *args, **kw):
        """ Profile a single function call.
        """
        self.enable_by_count()
        try:
            return func(*args, **kw)
        finally:
            self.disable_by_count()

    def add_module(self, mod):
        """ Add all the functions in a module and its classes.
        """
        from inspect import isclass, isfunction

        nfuncsadded = 0
        for item in mod.__dict__.values():
            if isclass(item):
                for k, v in item.__dict__.items():
                    if isfunction(v):
                        self.add_function(v)
                        nfuncsadded += 1
            elif isfunction(item):
                self.add_function(item)
                nfuncsadded += 1

        return nfuncsadded

empty = ('', '', 0, 0, '')

def show_func(filename, start_lineno, func_name, timings, unit, stream=sys.stdout, stripzeros=False, options=None):
    """ Show results for a single function.
    """
    do_block_sums = options and options.block_sum
    line_stats = {}
    total_time = 0.0
    linenos = []
    for lineno, nhits, time in timings:
        total_time += time
        linenos.append(lineno)

    if stripzeros and total_time == 0:
        return

    stream.write("Total time: %g s\n" % (total_time * unit))
    if os.path.exists(filename) or filename.startswith("<ipython-input-"):
        stream.write("File: %s\n" % filename)
        stream.write("Function: %s at line %s\n" % (func_name, start_lineno))
        if os.path.exists(filename):
            # Clear the cache to ensure that we get up-to-date results.
            linecache.clearcache()
        all_lines = linecache.getlines(filename)
        sublines = inspect.getblock(all_lines[start_lineno-1:])
    else:
        stream.write("\n")
        stream.write("Could not find file %s\n" % filename)
        stream.write("Are you sure you are running this program from the same directory\n")
        stream.write("that you ran the profiler from?\n")
        stream.write("Continuing without the function's contents.\n")
        # Fake empty lines so we can see the timings, if not the code.
        nlines = max(linenos) - min(min(linenos), start_lineno) + 1
        sublines = [''] * nlines

    max_line_len = 0
    for l in sublines:
        max_line_len = max(max_line_len, len(l.rstrip('\n').rstrip('\r')))
    max_line_len += 2

    template = '%(line)6s %(hits)9s %(time)12s %(per_hit)10s %(p_time)8s  %(line_contents)-s'
    if do_block_sums:
        template = '%%(line)6s %%(hits)9s %%(time)12s %%(per_hit)10s %%(p_time)8s %%(block_sum)11s  %%(block_sum_hit)-14s %%(line_contents)-%ss %%(comment)s' % max_line_len

    header_keys = {"line": "Line #",
                   "hits": "Hits",
                   "time": "Time",
                   "per_hit": "Per Hit",
                   "p_time": "% Time",
                   "block_sum": "Block Sum",
                   "block_sum_hit": "Block Sum/Hit",
                   "line_contents": "Line Contents",
                   "comment": ""}

    linenos = range(start_lineno, start_lineno + len(sublines))

    for lineno, nhits, time in timings:
        line_stats[lineno] = (nhits, time, (float(time) / nhits), ((100*time / total_time) if time else 0), [])

    if do_block_sums:
        calculate_block_sums(line_stats, linenos, sublines)

    def grouped_number(val):
        if val == '' or val == 0:
            return ""
        if type(val) == float:
            return locale.format("%0.1f", val, grouping=True if options and options.grouped_numbers else False)
        return locale.format("%d", val, grouping=True if options and options.grouped_numbers else False)

    lines_by_times = {}
    header = template % header_keys

    print("", file=stream)
    print(header, file=stream)
    print('=' * len(header), file=stream)

    comment = ""
    for lineno, line in zip(linenos, sublines):
        nhits, time, per_hit, percent, level_sum = line_stats.get(lineno, empty)
        block_sum = 0
        block_sum_per_hit = 0

        if time:
            time = int(time)

        if do_block_sums:
            for s in level_sum:
                block_sum += s

            if block_sum > 0:
                block_sum += time
                block_sum_per_hit = block_sum/float(nhits)

            if time and block_sum:
                lines_by_times[block_sum] = lineno

        print(template % {"line": lineno,
                          "hits": grouped_number(nhits),
                          "time": grouped_number(time),
                          "per_hit": '%s' % grouped_number(per_hit),
                          "p_time": grouped_number(percent),
                          "block_sum": grouped_number(block_sum),
                          "block_sum_hit": grouped_number(block_sum_per_hit),
                          "line_contents": line.rstrip('\n').rstrip('\r'),
                          "comment": comment},
              file=stream)
    print("", file=stream)

    if options and options.print_sorted_blocks:
        # Print the line numbers with biggest sums
        ts = reversed(sorted(lines_by_times.keys()))
        for i, t in enumerate(ts):
            if i == int(options.print_sorted_blocks):
                break
            print("Line %s, block sum: %s" % (lines_by_times[t], t), file=stream)

def calculate_block_sums(line_stats, linenos, sublines):
    sum_level = [] # Contains tuples of (indent, linenumber, sum)
    prev_indent = -1

    # Calculate the sums
    for i in range(len(sublines)):
        line = sublines[i]
        lineno = linenos[i]
        t_sum = []

        def space_count(line):
            """Finds the indent level for a source line"""
            m = re.match(r"(\s+)", line.lstrip("\n"))
            if not m:
                return 0
            spaces = m.group(1)
            return len(spaces)

        # Ignore empty lines and commented lines
        if not line.rstrip() or line.startswith("#"):
            continue

        indent = space_count(line)
        # We are up at least one level. Remove indents from sum_level
        if indent < prev_indent:
            for a in xrange(len(sum_level) - 1, -1, -1):
                indent_l, lineno_l, t_sum = sum_level[a]
                if indent_l >= indent:
                    del sum_level[a]
        prev_indent = indent

        if lineno in line_stats:
            time = line_stats[lineno][1]
            # Add the time for this line to previous sum levels
            for l in sum_level:
                l[2].append(time)

        # We want to show the sum for the following blocks
        if not re.match(r'^(def |for |while |if |else:|elif )', line.strip()):
            continue
        # If the next has the same indent we know its a multiline comment, so ignore
        if len(sublines) > i+1 and space_count(sublines[i+1]) == indent:
            continue

        # Missing in stats
        if not lineno in line_stats:
            # If it's an else, we take the nhits from next line with stats
            if re.match(r'^(else:)', line.strip()):
                indent = space_count(line)
                # Find first line with times after this
                print_  = True
                for u in range(i +1, len(sublines)):
                    next_indent = space_count(sublines[u])
                    # Multiline comments can have empty lines
                    # Next indent is less (higher level)
                    if next_indent != 0 and next_indent < indent:
                        # We didn't find any lines with with timings for this block
                        break
                    if not linenos[u] in line_stats:
                        continue
                    nhits, time, per_hit, percent, level_sum = line_stats.get(linenos[u], empty)
                    line_stats[lineno] = (nhits, 0, 0, 0, [])
                    break
            elif re.match(r'^(def )', line.strip()):
                if i == 0:  # If def is on first line, cannot check previous
                    continue
                prev_line = sublines[i - 1]
                prev_lineno = linenos[i - 1]

                # With profile decorator, the stats are saved on the @profile line
                # and not the def line. Move the values from @profile line to def line
                if re.match(r'^(@profile)', prev_line.strip()):
                    # No support for block sum in generator functions
                    if prev_lineno in line_stats:
                        line_stats[lineno] = line_stats[prev_lineno]
                        del line_stats[prev_lineno]

        if lineno in line_stats:
            sum_level.insert(0, (indent, lineno, line_stats[lineno][4]))


def show_text(stats, unit, stream=None, stripzeros=False, options=None):
    """ Show text for the given timings.
    """
    if stream is None:
        stream = sys.stdout

    stream.write('Timer unit: %g s\n\n' % unit)
    for (fn, lineno, name), timings in sorted(stats.items()):
        show_func(fn, lineno, name, stats[fn, lineno, name], unit, stream=stream, stripzeros=stripzeros, options=options)

# A %lprun magic for IPython.
def magic_lprun(self, parameter_s=''):
    """ Execute a statement under the line-by-line profiler from the
    line_profiler module.

    Usage:
      %lprun -f func1 -f func2 <statement>

    The given statement (which doesn't require quote marks) is run via the
    LineProfiler. Profiling is enabled for the functions specified by the -f
    options. The statistics will be shown side-by-side with the code through the
    pager once the statement has completed.

    Options:

    -f <function>: LineProfiler only profiles functions and methods it is told
    to profile.  This option tells the profiler about these functions. Multiple
    -f options may be used. The argument may be any expression that gives
    a Python function or method object. However, one must be careful to avoid
    spaces that may confuse the option parser. Additionally, functions defined
    in the interpreter at the In[] prompt or via %run currently cannot be
    displayed.  Write these functions out to a separate file and import them.

    -m <module>: Get all the functions/methods in a module

    One or more -f or -m options are required to get any useful results.

    -D <filename>: dump the raw statistics out to a pickle file on disk. The
    usual extension for this is ".lprof". These statistics may be viewed later
    by running line_profiler.py as a script.

    -T <filename>: dump the text-formatted statistics with the code side-by-side
    out to a text file.

    -r: return the LineProfiler object after it has completed profiling.

    -s: strip out all entries from the print-out that have zeros.
    """
    # Local imports to avoid hard dependency.
    from distutils.version import LooseVersion
    import IPython
    ipython_version = LooseVersion(IPython.__version__)
    if ipython_version < '0.11':
        from IPython.genutils import page
        from IPython.ipstruct import Struct
        from IPython.ipapi import UsageError
    else:
        from IPython.core.page import page
        from IPython.utils.ipstruct import Struct
        from IPython.core.error import UsageError

    # Escape quote markers.
    opts_def = Struct(D=[''], T=[''], f=[], m=[])
    parameter_s = parameter_s.replace('"', r'\"').replace("'", r"\'")
    opts, arg_str = self.parse_options(parameter_s, 'rsf:m:D:T:', list_all=True)
    opts.merge(opts_def)

    global_ns = self.shell.user_global_ns
    local_ns = self.shell.user_ns

    # Get the requested functions.
    funcs = []
    for name in opts.f:
        try:
            funcs.append(eval(name, global_ns, local_ns))
        except Exception as e:
            raise UsageError('Could not find function %r.\n%s: %s' % (name,
                e.__class__.__name__, e))

    profile = LineProfiler(*funcs)

    # Get the modules, too
    for modname in opts.m:
        try:
            mod = __import__(modname, fromlist=[''])
            profile.add_module(mod)
        except Exception as e:
            raise UsageError('Could not find module %r.\n%s: %s' % (modname,
                e.__class__.__name__, e))

    # Add the profiler to the builtins for @profile.
    if PY3:
        import builtins
    else:
        import __builtin__ as builtins

    if 'profile' in builtins.__dict__:
        had_profile = True
        old_profile = builtins.__dict__['profile']
    else:
        had_profile = False
        old_profile = None
    builtins.__dict__['profile'] = profile

    try:
        try:
            profile.runctx(arg_str, global_ns, local_ns)
            message = ''
        except SystemExit:
            message = """*** SystemExit exception caught in code being profiled."""
        except KeyboardInterrupt:
            message = ("*** KeyboardInterrupt exception caught in code being "
                "profiled.")
    finally:
        if had_profile:
            builtins.__dict__['profile'] = old_profile

    # Trap text output.
    stdout_trap = StringIO()
    profile.print_stats(stdout_trap, stripzeros='s' in opts)
    output = stdout_trap.getvalue()
    output = output.rstrip()

    if ipython_version < '0.11':
        page(output, screen_lines=self.shell.rc.screen_length)
    else:
        page(output)
    print(message, end="")

    dump_file = opts.D[0]
    if dump_file:
        profile.dump_stats(dump_file)
        print('\n*** Profile stats pickled to file %r. %s' % (
            dump_file, message))

    text_file = opts.T[0]
    if text_file:
        pfile = open(text_file, 'w')
        pfile.write(output)
        pfile.close()
        print('\n*** Profile printout saved to text file %r. %s' % (
            text_file, message))

    return_value = None
    if 'r' in opts:
        return_value = profile

    return return_value


def load_ipython_extension(ip):
    """ API for IPython to recognize this module as an IPython extension.
    """
    ip.define_magic('lprun', magic_lprun)


def load_stats(filename):
    """ Utility function to load a pickled LineStats object from a given
    filename.
    """
    with open(filename, 'rb') as f:
        return pickle.load(f)


def add_line_profile_options(parser):
    parser.add_argument('--version', action='version', version='%%(prog)s %s' % _version)
    parser.add_argument("-g", "--grouped-numbers",
                        action="store_true", default=False,
                        help="Print numbers in groups")
    parser.add_argument("--block-sum",
                        action="store_true", default=False,
                        help="Show code block sums")
    parser.add_argument("--print-sorted-blocks", nargs="?", const=5, type=int,
                        help="Print block sums sorted by time (Default blocks to print: %(const)s)")

def main():
    parser = argparse.ArgumentParser(description='Show profile output')
    parser.add_argument('filename', help='Filename')
    add_line_profile_options(parser)

    args = parser.parse_args()
    lstats = load_stats(args.filename)
    show_text(lstats.timings, lstats.unit, options=args)

if __name__ == '__main__':
    main()
