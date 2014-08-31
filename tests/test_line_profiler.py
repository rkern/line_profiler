import unittest

from line_profiler import LineProfiler


def f(x):
    y = x + 10
    return y


def g(x):
    y = yield x + 10
    yield y + 20


class TestLineProfiler(unittest.TestCase):

    def test_init(self):
        lp = LineProfiler()
        self.assertEqual(lp.functions, [])
        self.assertEqual(lp.code_map, {})
        lp = LineProfiler(f)
        self.assertEqual(lp.functions, [f])
        self.assertEqual(lp.code_map, {f.__code__: {}})
        lp = LineProfiler(f, g)
        self.assertEqual(lp.functions, [f, g])
        self.assertEqual(lp.code_map, {
            f.__code__: {},
            g.__code__: {},
        })

    def test_enable_disable(self):
        lp = LineProfiler()
        self.assertEqual(lp.enable_count, 0)
        lp.enable_by_count()
        self.assertEqual(lp.enable_count, 1)
        lp.enable_by_count()
        self.assertEqual(lp.enable_count, 2)
        lp.disable_by_count()
        self.assertEqual(lp.enable_count, 1)
        lp.disable_by_count()
        self.assertEqual(lp.enable_count, 0)
        self.assertEqual(lp.last_time, {})
        lp.disable_by_count()
        self.assertEqual(lp.enable_count, 0)

        with lp:
            self.assertEqual(lp.enable_count, 1)
            with lp:
                self.assertEqual(lp.enable_count, 2)
            self.assertEqual(lp.enable_count, 1)
        self.assertEqual(lp.enable_count, 0)
        self.assertEqual(lp.last_time, {})

        with self.assertRaises(RuntimeError):
            self.assertEqual(lp.enable_count, 0)
            with lp:
                self.assertEqual(lp.enable_count, 1)
                raise RuntimeError()
        self.assertEqual(lp.enable_count, 0)
        self.assertEqual(lp.last_time, {})

    def test_function_decorator(self):
        profile = LineProfiler()
        f_wrapped = profile(f)
        self.assertEqual(f_wrapped.__name__, 'f')

        self.assertEqual(profile.enable_count, 0)
        value = f_wrapped(10)
        self.assertEqual(profile.enable_count, 0)
        self.assertEqual(value, f(10))

        timings = profile.code_map[f.__code__]
        self.assertEqual(len(timings), 2)
        for timing in timings.values():
            self.assertEqual(timing.nhits, 1)

    def test_gen_decorator(self):
        profile = LineProfiler()
        g_wrapped = profile(g)
        self.assertEqual(g_wrapped.__name__, 'g')
        timings = profile.code_map[g.__code__]

        self.assertEqual(profile.enable_count, 0)
        i = g_wrapped(10)
        self.assertEqual(profile.enable_count, 0)
        self.assertEqual(next(i), 20)
        self.assertEqual(profile.enable_count, 0)
        self.assertEqual(len(timings), 1)
        self.assertEqual(i.send(30), 50)
        self.assertEqual(profile.enable_count, 0)
        self.assertEqual(len(timings), 2)
        with self.assertRaises(StopIteration):
            next(i)
        self.assertEqual(profile.enable_count, 0)

        self.assertEqual(len(timings), 2)
        for timing in timings.values():
            self.assertEqual(timing.nhits, 1)
