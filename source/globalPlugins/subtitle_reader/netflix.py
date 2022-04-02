#coding=utf-8

from .subtitle_alg import SubtitleAlg
from .object_finder import find
from .compatible import role

class Netflix(SubtitleAlg):
	def getVideoPlayer(self):
		obj = self.main.focusObject
		videoPlayer = find(obj, 'parent', 'role', role('dialog'))
		if not videoPlayer:
			videoPlayer = find(obj, 'parent', 'role', role('document'))
		
		return videoPlayer
	
	def getSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		appName = videoPlayer.appModule.appName
		return getattr(self, appName + 'GetSubtitleContainer')()
	
	def chromeGetSubtitleContainer(self):
		obj = self.main.videoPlayer
		obj = find(obj, 'firstChild', 'role', role('grouping'))
		return obj
	
	def firefoxGetSubtitleContainer(self):
		obj = self.main.videoPlayer
		obj = find(obj, 'firstChild', 'role', role('grouping'))
		return obj
	
	def getSubtitle(self):
		subtitle = ''
		obj = self.main.subtitleContainer
		obj = obj.next
		while obj and not obj.name:
			try:
				obj = obj.firstChild
			except:
				obj = None
			
		
		pobj = obj
		while obj:
			if obj.name:
				subtitle += obj.name + '\r\n'
			
			pobj = obj
			obj = obj.next
		
		if not pobj.name:
			return
		
		return subtitle
	
