#!/usr/bin/python

import json
import logging
import os
import pickle
import pprint
import re
import sys
import tempfile
import time
import traceback

from stompest.config import StompConfig
from stompest.sync import Stomp

HTML_HEAD = """
<HTML>
<HEAD>
<meta http-equiv="refresh" content="10">
</head> 
<BODY>
<TABLE>
"""

HTML_FOOT = """
</TABLE>
</HTML>
"""

class networkMapper(object):
	def __init__(self):
		self._edges = []
		self._berths = {}
		self._client = None

	def configureClient(self, _login, _passcode):
		CONFIG = StompConfig('tcp://datafeeds.networkrail.co.uk:61618', login=_login, passcode=_passcode)
		
		client = Stomp(CONFIG)
		client.connect()
		client.subscribe('/topic/TD_KENT_MCC_SIG_AREA')

		self._client = client

	def processMessage(self, msg_type, msg):
		headcode = msg['descr']
		if True or headcode in sys.argv:
			area = msg['area_id']
			if area in ['LB', 'AD']:
				_from = '%s%s' % (area, msg['from'])
				_to = '%s%s' % (area, msg['to']	)
				print '%s %s: %s --> %s' % (msg_type, headcode, _from, _to)

				if (_from in self._berths) and (self._berths[_from] == headcode):
					self._berths[_from] = None

				self._berths[_to] = headcode

	def procFrame(self):
			try:
				frame = self._client.receiveFrame()
				data = json.loads(frame.body)
				for msg in data:
					for k in msg:
						if k.startswith('CA'):
							try:
								self.processMessage(k, msg[k])
							except Exception, e:
								pprint.pprint(msg)
								raise
			except Exception, e:
				pprint.pprint(data)
				raise

	def disconnect(self):
		self._client.disconnect()

	def loadEdges(self):
		try:
			self._edges = pickle.load(open('edges', 'r'))
			self._graphFlag = True
		except:
			print >> sys.stderr, 'Could not load edges'
			self._edges = []

	def dumpEdges(self):
		pickle.dump(self._edges, open('edges', 'w'))

	def dumpTable(self):
		f = open('/var/www/html/2S.html', 'w')
		f.write(HTML_HEAD)
		hc = {}
		for b in self._berths:
			if self._berths[b] is not None:
				hc[self._berths[b]] = b

		for h in sorted(hc.keys()):
			f.write('<TR><TD>%s</TD><TD>%s</TD></TR>' % (h, hc[h]))
			
		f.write(HTML_FOOT)
		f.close()

def main():

	logging.basicConfig()
	logging.getLogger().setLevel(logging.INFO)

	passcode = open('passcode', 'r').read().strip()
	userid = open('userid', 'r').read().strip()

	m = networkMapper()
	m.configureClient(userid, passcode)
	m.loadEdges()
	try:
		while True:
			m.procFrame()
			m.dumpTable()
	finally:
		print >> sys.stderr, 'Disconnecting...'
		m.disconnect()
	
	m.dumpEdges()

if __name__ == '__main__':
	main()
