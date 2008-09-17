from cProfile import label
import marshal

from _line_profiler import LineProfiler as CLineProfiler


class LineProfiler(CLineProfiler):
    """ A subclass of the C version solely to provide a decorator since Cython
    does not have closures.
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
        stats = self.get_stats()
        f = open(filename, 'wb')
        try:
            marshal.dump(stats, f)
        finally:
            f.close()

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

