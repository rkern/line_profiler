import unittest
import sys

from kernprof import ContextualProfile

PY3 = sys.version_info[0] == 3
PY35 = PY3 and sys.version_info[1] >= 5


def f(x):
    """ A function. """
    y = x + 10
    return y


def g(x):
    """ A generator. """
    y = yield x + 10
    yield y + 20


class TestKernprof(unittest.TestCase):

    def test_enable_disable(self):
        profile = ContextualProfile()
        self.assertEqual(profile.enable_count, 0)
        profile.enable_by_count()
        self.assertEqual(profile.enable_count, 1)
        profile.enable_by_count()
        self.assertEqual(profile.enable_count, 2)
        profile.disable_by_count()
        self.assertEqual(profile.enable_count, 1)
        profile.disable_by_count()
        self.assertEqual(profile.enable_count, 0)
        profile.disable_by_count()
        self.assertEqual(profile.enable_count, 0)

        with profile:
            self.assertEqual(profile.enable_count, 1)
            with profile:
                self.assertEqual(profile.enable_count, 2)
            self.assertEqual(profile.enable_count, 1)
        self.assertEqual(profile.enable_count, 0)

        with self.assertRaises(RuntimeError):
            self.assertEqual(profile.enable_count, 0)
            with profile:
                self.assertEqual(profile.enable_count, 1)
                raise RuntimeError()
        self.assertEqual(profile.enable_count, 0)

    def test_function_decorator(self):
        profile = ContextualProfile()
        f_wrapped = profile(f)
        self.assertEqual(f_wrapped.__name__, f.__name__)
        self.assertEqual(f_wrapped.__doc__, f.__doc__)

        self.assertEqual(profile.enable_count, 0)
        value = f_wrapped(10)
        self.assertEqual(profile.enable_count, 0)
        self.assertEqual(value, f(10))

    def test_gen_decorator(self):
        profile = ContextualProfile()
        g_wrapped = profile(g)
        self.assertEqual(g_wrapped.__name__, g.__name__)
        self.assertEqual(g_wrapped.__doc__, g.__doc__)

        self.assertEqual(profile.enable_count, 0)
        i = g_wrapped(10)
        self.assertEqual(profile.enable_count, 0)
        self.assertEqual(next(i), 20)
        self.assertEqual(profile.enable_count, 0)
        self.assertEqual(i.send(30), 50)
        self.assertEqual(profile.enable_count, 0)
        with self.assertRaises(StopIteration):
            next(i)
        self.assertEqual(profile.enable_count, 0)

    if PY35:
        def test_coroutine_decorator(self):
            async def _():
                async def c(x):
                    """ A coroutine. """
                    y = x + 10
                    return y

                profile = ContextualProfile()
                c_wrapped = profile(c)
                self.assertEqual(c_wrapped.__name__, c.__name__)
                self.assertEqual(c_wrapped.__doc__, c.__doc__)

                self.assertEqual(profile.enable_count, 0)
                value = await c_wrapped(10)
                self.assertEqual(profile.enable_count, 0)
                self.assertEqual(value, await c(10))

            import asyncio
            loop = asyncio.get_event_loop()
            loop.run_until_complete(_())
            loop.close()


if __name__ == '__main__':
    unittest.main()
