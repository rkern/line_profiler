#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import inspect
import linecache
import marshal
import os

from _line_profiler import LineProfiler as CLineProfiler


def label(code):
    """ Return a (filename, first_lineno, func_name) tuple for a given code
    object.

    This is the same labelling as used by the cProfile module in Python 2.5.
    """
    if isinstance(code, str):
        return ('~', 0, code)    # built-in functions ('~' sorts at the end)
    else:
        return (code.co_filename, code.co_firstlineno, code.co_name)

class LineProfiler(CLineProfiler):
    """ A profiler that records the execution times of individual lines.
    """

    def __call__(self, func):
        """ Decorate a function to start the profiler on function entry and stop
        it on function exit.
        """
        def f(*args, **kwds):
            self.add_function(func)
            self.enable_by_count()
            try:
                result = func(*args, **kwds)
            finally:
                self.disable_by_count()
            return result
        f.__name__ = func.__name__
        f.__doc__ = func.__doc__
        f.__dict__.update(func.__dict__)
        return f

    def dump_stats(self, filename):
        """ Dump a representation of the data to a file as a marshalled
        dictionary from `get_stats()`.
        """
        stats, unit = self.get_stats()
        f = open(filename, 'wb')
        try:
            marshal.dump((stats, unit), f)
        finally:
            f.close()

    def print_stats(self):
        """ Show the gathered statistics.
        """
        stats, unit = self.get_stats()
        show_text(stats, unit)

    def run(self, cmd):
        """ Profile a single executable statment in the main namespace.
        """
        import __main__
        dict = __main__.__dict__
        return self.runctx(cmd, dict, dict)

    def runctx(self, cmd, globals, locals):
        """ Profile a single executable statement in the given namespaces.
        """
        self.enable_by_count()
        try:
            exec cmd in globals, locals
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


def show_func(filename, start_lineno, func_name, timings, unit):
    """ Show results for a single function.
    """
    if not os.path.exists(filename):
        print 'Could not find file %s' % filename
        print 'Are you sure you are running this program from the same directory'
        print 'that you ran the profiler from?'
        return
    print 'File: %s' % filename
    print 'Function: %s at line %s' % (func_name, start_lineno)
    all_lines = linecache.getlines(filename)
    sublines = inspect.getblock(all_lines[start_lineno-1:])
    template = '%6s %9s %12s %8s  %-s'
    d = {}
    total_time = 0.0
    for lineno, nhits, time in timings:
        total_time += time
    print 'Total time: %g s' % (total_time * unit)
    for lineno, nhits, time in timings:
        d[lineno] = (nhits, time, '%5.1f' % (100*time / total_time))
    linenos = range(start_lineno, start_lineno + len(sublines))
    empty = ('', '', '')
    header = template % ('Line #', 'Hits', 'Time', '% Time', 'Line Contents')
    print
    print header
    print '=' * len(header)
    for lineno, line in zip(linenos, sublines):
        nhits, time, percent = d.get(lineno, empty)
        print template % (lineno, nhits, time, percent, line.rstrip('\n').rstrip('\r'))
    print

def show_text(stats, unit):
    """ Show text for the given timings.
    """
    print 'Timer unit: %g s' % unit
    print
    for (fn, lineno, name), timings in sorted(stats.items()):
        show_func(fn, lineno, name, stats[fn, lineno, name], unit)

def main():
    import optparse
    usage = "usage: %prog [-t] profile.lprof"
    parser = optparse.OptionParser(usage)
    parser.add_option('-t', '--text', action='store_const', const='text',
        dest='action', default='text', help="Show text output.")

    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error("Must provide a filename.")
    f = open(args[0], 'rb')
    stats, unit = marshal.load(f)
    f.close()
    if options.action == 'text':
        show_text(stats, unit)
    else:
        parser.error("Only --text is supported at this time.")

if __name__ == '__main__':
    main()
