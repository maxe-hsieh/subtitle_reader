#coding=utf-8

from .subtitle_alg import SubtitleAlg
from .object_finder import find
from .compatible import role

class DisneyPlus(SubtitleAlg):
	def getVideoPlayer(self):
		obj = self.main.focusObject
		try:
			while obj and obj.role != role('document'):
				obj = obj.parent
			
		
		except:
			return
		
		return obj
	
	def getSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		appName = videoPlayer.appModule.appName
		return getattr(self, appName + 'GetSubtitleContainer')()
	
	def chromeGetSubtitleContainer(self):
		obj = self.main.videoPlayer
		obj = find(obj, 'firstChild', 'class', 'sc-cjHlYL khuMjN')
		obj = obj.next
		obj = obj.firstChild.firstChild.firstChild.firstChild
		obj = obj.next
		if obj.IA2Attributes.get('class') == 'dss-hls-subtitle-overlay':
			return obj
		
	
	def firefoxGetSubtitleContainer(self):
		obj = self.main.videoPlayer
		obj = find(obj, 'firstChild', 'role', 56)
		obj = obj.next
		if obj.IA2Attributes.get('class') == 'dss-hls-subtitle-overlay':
			return obj
		
	
