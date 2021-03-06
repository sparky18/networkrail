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

import matplotlib
matplotlib.use('Agg')
import networkx as nx
import matplotlib.pyplot as plt

from  networkx.algorithms.traversal.depth_first_search import dfs_tree

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

	def oddNumber(self, s):
		m = re.search('[13579]$', s)
		return m is not None

	def evenNumber(self, s):
		m = re.search('[13579]$', s)
		return m is None

	def outputFile(self, plt, filename):
		f = tempfile.NamedTemporaryFile(delete=False, prefix='/var/www/html/')
		plt.savefig(f, bbox_inches='tight', format='png') # save as png
		f.close()
		os.chmod(f.name, 292) # 444
		if os.path.exists(filename):
			os.unlink(filename)
		os.link(f.name, filename)
		os.unlink(f.name)

	def outputGraph(self, filename, _filter=None):
		if filename not in self._graphTime:
			self._graphTime[filename] = 0

		if (time.time() - self._graphTime[filename]) > 10:
			# print 'pre-Update Graph: %s' % filename
			G = nx.DiGraph()
			plt.clf()
			for edge in self._edges:
				if _filter is None:
					G.add_edge(edge[0], edge[1])
				elif _filter(edge[0]) or _filter(edge[1]):
					G.add_edge(edge[0], edge[1])

			try:
				G1 = dfs_tree(G, u'0015')
				G2 = dfs_tree(G, u'0013')
				G3 = nx.compose(G1,G2)
				G4 = dfs_tree(G, u'0017')
				G = nx.compose(G3, G4)
			except:
				pass

			relabel = {}
			newToOld = {}
			for n in G.nodes():
				if n in self._berths and self._berths[n] is not None:
					relabel[n] = self._berths[n]
					newToOld[self._berths[n]] = n
			nx.relabel_nodes(G, relabel, False)

			colours = []
			for n in G.nodes():
				if n in newToOld:
					n = newToOld[n]
				if n in self._berths and self._berths[n] is not None:
					colours.append('r')
				else:
					colours.append('g')

			pos = nx.graphviz_layout(G, prog='dot')

			nx.draw_networkx_nodes(G,pos, node_color=colours, node_shape='s', node_size=900)
			nx.draw_networkx_edges(G,pos)
			nx.draw_networkx_labels(G,pos)

			fig = matplotlib.pyplot.gcf()
			fig.set_size_inches(16.0, 25.0)
			plt.axis('off')
				
			self.outputFile(plt, filename)

			self._graphTime[filename] = time.time()
			# print 'Graph Updated: %s' % filename
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
				for msg in data:
					for k in msg:
						# if k.startswith(('CA', 'CB', 'CC')):
						if k.startswith('CA'):
							try:
								self.processMessage(k, msg[k])
							except Exception, e:
								pprint.pprint(msg)
								raise
				self.outputGraph('/var/www/html/down.png', self.oddNumber)
				self.outputGraph('/var/www/html/up.png', self.evenNumber)
			except KeyboardInterrupt:
				break
			except Exception, e:
				pprint.pprint(data)
				raise

	def disconnect(self):
		self._client.disconnect()

	def dumpEdges(self):
		pickle.dump(self._edges, open('edges', 'w'))

def main():


	logging.basicConfig()
	logging.getLogger().setLevel(logging.INFO)


	passcode = open('passcode', 'r').read().strip()
	userid = open('userid', 'r').read().strip()

	m = networkMapper()
	m.configureClient(userid, passcode)
	m.loadEdges()
	try:
		m.go()
	finally:
		print >> sys.stderr, 'Disconnecting...'
		m.disconnect()
	
	m.dumpEdges()

if __name__ == '__main__':
	main()
