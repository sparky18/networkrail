#!/usr/bin/python

import json
import logging
import pickle
import pprint
import re
import sys
import time
import traceback

from stompest.config import StompConfig
from stompest.sync import Stomp

import matplotlib
matplotlib.use('Agg')
import networkx as nx
import matplotlib.pyplot as plt

class networkMapper(object):
	def __init__(self):
		self._edges = []
		self._berths = {}
		self._client = None
		self._graphFlag = False
		self._graphTime = {}

	def configureClient(self, _login, _passcode):
		CONFIG = StompConfig('tcp://datafeeds.networkrail.co.uk:61618', login=_login, passcode=_passcode)
		
		client = Stomp(CONFIG)
		client.connect()
		client.subscribe('/topic/TD_KENT_MCC_SIG_AREA')

		self._client = client

	def loadEdges(self):
		try:
			self._edges = pickle.load(open('edges', 'r'))
			self._graphFlag = True
		except:
			print >> sys.stderr, 'Could not load edges'
			self._edges = []

	def updateGraph(self, area, _from, _to):
		try:
			if area != 'LB':
				return

			mFrom = re.match('(\d+)', _from)
			if mFrom is None:
				print _from
				return
			mTo = re.match('(\d+)', _to)
			if mTo is None:
				print _to
				return
			
			iFrom = int(mFrom.groups()[0])
			iTo   = int(mTo.groups()[0])

			pair = (_from, _to)
			if iFrom <= 220:
				if pair not in self._edges:
					self._edges.append(pair)
					self._graphFlag = True

		except Exception, e:
			print e
			print area, _from, _to
			print 'erk'

	def oddNumber(self, s):
		m = re.search('[13579]$', s)
		return m is not None

	def evenNumber(self, s):
		m = re.search('[13579]$', s)
		return m is None

	def outputGraph(self, filename, _filter=None):
		if filename not in self._graphTime:
			self._graphTime[filename] = 0

		if self._graphFlag:
			G = nx.DiGraph()
			plt.clf()
			for edge in self._edges:
				if _filter is None:
					G.add_edge(edge[0], edge[1])
				elif _filter(edge[0]) or _filter(edge[1]):
					G.add_edge(edge[0], edge[1])

			pos = nx.graphviz_layout(G, prog='dot')

			occupied = filter(lambda x: x in self._berths and self._berths[x] is not None, G.nodes())
			vacant   = filter(lambda x: x not in occupied, G.nodes())

			nx.draw_networkx_nodes(G,pos, nodelist=occupied, node_color='r', node_shape='s', node_size=900)
			nx.draw_networkx_nodes(G,pos, nodelist=vacant, node_color='g', node_shape='s', node_size=900)
			nx.draw_networkx_edges(G,pos)
			nx.draw_networkx_labels(G,pos)

			fig = matplotlib.pyplot.gcf()
			fig.set_size_inches(16.0, 30.0)
			plt.axis('off')
			# plt.savefig("simple_path.png") # save as png
			if (time.time() - self._graphTime[filename]) > 10:
				plt.savefig(filename) # save as png
				self._graphTime[filename] = time.time()
				print 'Graph Updated'
			# self._graphFlag = False

	def processMessage(self, msg_type, msg):
		headcode = msg['descr']
		if True or headcode in sys.argv:
			area = msg['area_id']
			if area == 'LB':
				_from = msg['from']	
				_to = msg['to']	
				print '%s %s: %s%s --> %s%s' % (msg_type, headcode, area, _from, area, _to)

				if (_from in self._berths) and (self._berths[_from] == headcode):
					self._berths[_from] = None

				self._berths[_to] = headcode
				self.updateGraph(area, _from, _to)

	def go(self):
		while True:
			try:
				frame = self._client.receiveFrame()
				data = json.loads(frame.body)
				# pprint.pprint(data)
				for msg in data:
					for k in msg:
						# if k.startswith(('CA', 'CB', 'CC')):
						if k.startswith('CA'):
							try:
								self.processMessage(k, msg[k])
							except KeyboardInterrupt:
								print 'AAA'
								raise
							except Exception, e:
								print traceback.format_exc()
								pprint.pprint(msg)
								continue
				self.outputGraph('/var/www/down.png', self.oddNumber)
				self.outputGraph('/var/www/up.png', self.evenNumber)
			except KeyboardInterrupt:
				print 'BBB'
				break
			except Exception, e:
				print traceback.format_exc()
				pprint.pprint(data)
				continue

	def disconnect(self):
		self._client.disconnect()

	def dumpEdges(self):
		pickle.dump(self._edges, open('edges', 'w'))

def main():


	logging.basicConfig()
	logging.getLogger().setLevel(logging.ERROR)


	passcode = open('passcode', 'r').read().strip()

	m = networkMapper()
	m.configureClient('networkrail-data@psi.epsilon.org.uk', passcode)
	m.loadEdges()
	m.go()


	m.disconnect()
	m.dumpEdges()

if __name__ == '__main__':
	main()
