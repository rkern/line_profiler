from .python25 cimport PyFrameObject, PyObject, PyStringObject


cdef extern from "frameobject.h":
    ctypedef int (*Py_tracefunc)(object self, PyFrameObject *py_frame, int what, PyObject *arg)

cdef extern from "Python.h":
    ctypedef long long PY_LONG_LONG
    cdef bint PyCFunction_Check(object obj)

    cdef void PyEval_SetProfile(Py_tracefunc func, object arg)
    cdef void PyEval_SetTrace(Py_tracefunc func, object arg)

    ctypedef object (*PyCFunction)(object self, object args)

    ctypedef struct PyMethodDef:
        char *ml_name
        PyCFunction ml_meth
        int ml_flags
        char *ml_doc

    ctypedef struct PyCFunctionObject:
        PyMethodDef *m_ml
        PyObject *m_self
        PyObject *m_module

    # They're actually #defines, but whatever.
    cdef int PyTrace_CALL
    cdef int PyTrace_EXCEPTION
    cdef int PyTrace_LINE
    cdef int PyTrace_RETURN
    cdef int PyTrace_C_CALL
    cdef int PyTrace_C_EXCEPTION
    cdef int PyTrace_C_RETURN

cdef extern from "timers.h":
    PY_LONG_LONG hpTimer()
    double hpTimerUnit()

cdef extern from "unset_trace.h":
    void unset_trace()


def label(code):
    """ Return a (filename, first_lineno, func_name) tuple for a given code
    object.

    This is the same labelling as used by the cProfile module in Python 2.5.
    """
    if isinstance(code, str):
        return ('~', 0, code)    # built-in functions ('~' sorts at the end)
    else:
        return (code.co_filename, code.co_firstlineno, code.co_name)


cdef class LineTiming:
    """ The timing for a single line.
    """
    cdef public object code
    cdef public int lineno
    cdef public PY_LONG_LONG total_time
    cdef public long nhits

    def __init__(self, object code, int lineno):
        self.code = code
        self.lineno = lineno
        self.total_time = 0
        self.nhits = 0

    cdef hit(self, PY_LONG_LONG dt):
        """ Record a line timing.
        """
        self.nhits += 1
        self.total_time += dt

    def astuple(self):
        """ Convert to a tuple of (lineno, nhits, total_time).
        """
        return (self.lineno, self.nhits, self.total_time)

    def __repr__(self):
        return '<LineTiming for %r\n  lineno: %r\n  nhits: %r\n  total_time: %r>' % (self.code, self.lineno, self.nhits, <long>self.total_time)


# Note: this is a regular Python class to allow easy pickling.
class LineStats(object):
    """ Object to encapsulate line-profile statistics.

    Attributes
    ----------
    timings : dict
        Mapping from (filename, first_lineno, function_name) of the profiled
        function to a list of (lineno, nhits, total_time) tuples for each
        profiled line. total_time is an integer in the native units of the
        timer.
    unit : float
        The number of seconds per timer unit.
    """
    def __init__(self, timings, unit):
        self.timings = timings
        self.unit = unit


cdef class LineProfiler:
    """ Time the execution of lines of Python code.
    """
    cdef public list functions
    cdef public dict code_map
    cdef public dict last_time
    cdef public double timer_unit
    cdef public long enable_count

    def __init__(self, *functions):
        self.functions = []
        self.code_map = {}
        self.last_time = {}
        self.timer_unit = hpTimerUnit()
        self.enable_count = 0
        for func in functions:
            self.add_function(func)

    def add_function(self, func):
        """ Record line profiling information for the given Python function.
        """
        try:
            code = func.__code__
        except AttributeError:
            import warnings
            warnings.warn("Could not extract a code object for the object %r" % (func,))
            return
        if code not in self.code_map:
            self.code_map[code] = {}
            self.functions.append(func)

    def enable_by_count(self):
        """ Enable the profiler if it hasn't been enabled before.
        """
        if self.enable_count == 0:
            self.enable()
        self.enable_count += 1

    def disable_by_count(self):
        """ Disable the profiler if the number of disable requests matches the
        number of enable requests.
        """
        if self.enable_count > 0:
            self.enable_count -= 1
            if self.enable_count == 0:
                self.disable()

    def __enter__(self):
        self.enable_by_count()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disable_by_count()

    def enable(self):
        PyEval_SetTrace(python_trace_callback, self)

    def disable(self):
        self.last_time = {}
        unset_trace()

    def get_stats(self):
        """ Return a LineStats object containing the timings.
        """
        stats = {}
        for code in self.code_map:
            entries = self.code_map[code].values()
            key = label(code)
            stats[key] = [e.astuple() for e in entries]
            stats[key].sort()
        return LineStats(stats, self.timer_unit)


cdef class LastTime:
    """ Record the last callback call for a given line.
    """
    cdef int f_lineno
    cdef PY_LONG_LONG time

    def __cinit__(self, int f_lineno, PY_LONG_LONG time):
        self.f_lineno = f_lineno
        self.time = time


cdef int python_trace_callback(object self_, PyFrameObject *py_frame, int what,
    PyObject *arg):
    """ The PyEval_SetTrace() callback.
    """
    cdef LineProfiler self
    cdef object code, key
    cdef dict line_entries, last_time
    cdef LineTiming entry
    cdef LastTime old
    cdef PY_LONG_LONG time

    self = <LineProfiler>self_
    last_time = self.last_time

    if what == PyTrace_LINE or what == PyTrace_RETURN:
        code = <object>py_frame.f_code
        if code in self.code_map:
            time = hpTimer()
            if code in last_time:
                old = last_time[code]
                line_entries = self.code_map[code]
                key = old.f_lineno
                if key not in line_entries:
                    entry = LineTiming(code, old.f_lineno)
                    line_entries[key] = entry
                else:
                    entry = line_entries[key]
                entry.hit(time - old.time)
            if what == PyTrace_LINE:
                # Get the time again. This way, we don't record much time wasted
                # in this function.
                last_time[code] = LastTime(py_frame.f_lineno, hpTimer())
            else:
                # We are returning from a function, not executing a line. Delete
                # the last_time record. It may have already been deleted if we
                # are profiling a generator that is being pumped past its end.
                if code in last_time:
                    del last_time[code]

    return 0


