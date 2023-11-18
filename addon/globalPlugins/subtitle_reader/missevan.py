#coding=utf-8

from .subtitle_alg import SubtitleAlg
from .object_finder import find, search
from .compatible import role

class Missevan(SubtitleAlg):
	lastCollect = set()
	collect = set()
	collector = None
	
	def getVideoPlayer(self):
		obj = self.main.focusObject
		document = find(obj, 'parent', 'role', role('document'))
		videoPlayer = find(document, 'firstChild', 'id', 'header')
		return videoPlayer
	
	def getSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		container = videoPlayer.next.firstChild.firstChild.next
		return container
	
	def getSubtitle(self):
		obj = self.main.subtitleContainer
		if self.collector and not self.collector.isStopped:
			return
		
		subtitle = self.collect - self.lastCollect
		subtitle = ' | '.join(subtitle)
		self.onFoundSubtitle(subtitle)
		self.lastCollect = self.collect
		self.collect = set()
		self.collector = search(obj.firstChild, self.condition, child=False, onFound=self.onFound, continueOnFound=True)
		
	def condition(self, obj):
		return 'b-danmaku-center' in obj.IA2Attributes.get('class', '')
	
	def onFound(self, obj):
		obj = obj.firstChild
		if obj:
			name = obj.name
			if name:
				self.collect.add(obj.name)
			
		
	
