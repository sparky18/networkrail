#!/usr/bin/python

import daemon
import os
import subprocess
import time

os.nice(5)

myPath = os.path.abspath(__file__)

with daemon.DaemonContext():
	os.chdir(os.path.dirname(myPath))
	for i in range(0, 10):
		p = subprocess.Popen(['./watch.py'])
		p.wait()
		time.sleep(10)
