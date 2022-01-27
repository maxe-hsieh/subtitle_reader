#coding=utf-8

from .subtitle_alg import SubtitleAlg

class DisneyPlus(SubtitleAlg):
	def getVideoPlayer(self):
		obj = self.main.focusObject
		try:
			while obj and obj.role != 52:
				obj = obj.parent
			
		
		except:
			return
		
		return obj
	
	def getSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		appName = videoPlayer.appModule.appName
		return getattr(self, appName + 'GetSubtitleContainer')()
	
	def chromeGetSubtitleContainer(self):
		try:
			obj = self.main.videoPlayer.firstChild.firstChild.firstChild.firstChild
			obj = obj.next
			obj = obj.firstChild.firstChild.firstChild.firstChild
			obj = obj.next
			if obj.IA2Attributes.get('class') == 'dss-hls-subtitle-overlay':
				return obj
			
		except:
			return
		
	
	def firefoxGetSubtitleContainer(self):
		try:
			obj = self.main.videoPlayer.firstChild.firstChild.firstChild.firstChild.firstChild.firstChild
			obj = obj.next
			if obj.IA2Attributes.get('class') == 'dss-hls-subtitle-overlay':
				return obj
			
		except:
			return
		
	
