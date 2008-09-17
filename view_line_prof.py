#!/usr/bin/env python
# -*- coding: UTF-8 -*-
""" View line profile timings.
"""

import inspect
import linecache
import marshal
import os


def show_func(filename, start_lineno, func_name, timings):
    """ Show results for a single function.
    """
    if not os.path.exists(filename):
        print 'Could not find file %s' % filename
        return
    print 'File: %s' % filename
    print 'Function: %s at line %s' % (func_name, start_lineno)
    print
    all_lines = linecache.getlines(filename)
    sublines = inspect.getblock(all_lines[start_lineno-1:])
    header_template = '%6s %9s %12s %8s   %-s'
    entry_template = '%6s %9s %12s %8s   %-s'
    d = {}
    total_time = 0.0
    for lineno, nhits, time in timings:
        total_time += time
    for lineno, nhits, time in timings:
        d[lineno] = (nhits, time, '%5.1f' % (100*time / total_time))
    linenos = range(start_lineno, start_lineno + len(sublines))
    empty = ('', '', '')
    header = header_template % ('Line #', 'Hits', 'Time', '% Time', 'Line Contents')
    print header
    print '=' * len(header)
    for lineno, line in zip(linenos, sublines):
        nhits, time, percent = d.get(lineno, empty)
        print entry_template % (lineno, nhits, time, percent, line.rstrip('\n').rstrip('\r'))
    print

def show_text(args, stats, unit):
    """ Show text for the given timings.
    """
    print 'Timer unit: %g s' % unit
    print
    for (fn, lineno, name), timings in sorted(stats.items()):
        show_func(fn, lineno, name, stats[fn, lineno, name])


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--text', action='store_const', const='text',
        dest='action', default='text', help="Show text output.")
    parser.add_argument('proffile',
        help="The name of the line-profiler output file.")

    args = parser.parse_args()
    f = open(args.proffile, 'rb')
    stats, unit = marshal.load(f)
    f.close()
    if args.action == 'text':
        show_text(args, stats, unit)


if __name__ == '__main__':
    main()
