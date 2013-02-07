#!/usr/bin/python

import subprocess
import time

for i in range(0, 10):
	p = subprocess.Popen(['./watch.py'])
	p.wait()
	time.sleep(10)
