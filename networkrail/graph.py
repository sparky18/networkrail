#
#
#

import watch

import matplotlib
matplotlib.use('Agg')
import networkx as nx
import matplotlib.pyplot as plt

from  networkx.algorithms.traversal.depth_first_search import dfs_tree

class grapher(networkMapper):

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


	def go():
		while True:
			self.procFrame()
			self.outputGraph('/var/www/html/down.png', self.oddNumber)
			self.outputGraph('/var/www/html/up.png', self.evenNumber)
		
