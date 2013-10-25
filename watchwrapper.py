#!/usr/bin/python

import daemon
import os
import subprocess
import time

os.nice(5)

cwd = os.getcwd()

with daemon.DaemonContext():
	os.chdir(cwd)
	for i in range(0, 10):
		p = subprocess.Popen(['./watch.py'])
		p.wait()
		time.sleep(10)
