#!/usr/bin/python

import os
import subprocess
import time

os.nice(5)

for i in range(0, 10):
	p = subprocess.Popen(['./watch.py'])
	p.wait()
	time.sleep(10)
