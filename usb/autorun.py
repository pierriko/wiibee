#! /usr/bin/env python
""" Gather data and print them to stdout

req. https://github.com/pierriko/wiiboard

usage: autorun.py [-d] "00:1e:35:fd:11:fc" "00:22:4c:6e:12:6c" >> data.txt
"""
import sys
import time
import logging
import threading
import subprocess
from wiiboard import logger, WiiboardSampling

class WiiboardThreaded(WiiboardSampling):
    def __init__(self, address=None):
        self.thread = threading.Thread(target=self.loop)
        WiiboardSampling.__init__(self, address)
    def average(self):
        # Copy deque content by using list() copy constructor
        #   to avoid: RuntimeError: deque mutated during iteration
        samples = [sum(sample.values()) for sample in list(self.samples)]
        return sum(samples) / float(len(samples))

if '-d' in sys.argv:
    logger.setLevel(logging.DEBUG)
    sys.argv.remove('-d')

def try_or_zero(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error("%s error %s", func.__name__, e)
            return 0
    return wrapper

@try_or_zero
def cpu_temp(filepath='/sys/class/thermal/thermal_zone0/temp'):
    with open(filepath) as f:
        return float(f.read()) / 1000

@try_or_zero
def wtp_temp(): # TODO i2c read/write use `smbus`
    return float(subprocess.check_output(['/bin/bash', 'wtp_temp.sh', 'get']))

wiiboards = [WiiboardThreaded(address) for address in sys.argv[1:]]
# first connect then listen all balance, try to avoid connection refused error
[wiiboard.thread.start() for wiiboard in wiiboards]

for i in xrange(10):
    time.sleep(2)
    print("%.3f %.2f %.2f "%(time.time(), cpu_temp(), wtp_temp()) +
          " ".join(["%.2f"%wiiboard.average() for wiiboard in wiiboards]))

[wiiboard.close() for wiiboard in wiiboards]