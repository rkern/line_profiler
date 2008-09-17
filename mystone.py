#!/usr/bin/env python

import os
import pystone

#import lineprof

print os.getpid()
#lineprof.enable()

pystone.pystones()
