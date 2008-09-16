import pystone

from line_profiler import LineProfiler


lp = LineProfiler(pystone.Proc0)
lp.enable()
pystone.pystones()
lp.disable()
code = lp.code_map.keys()[0]

