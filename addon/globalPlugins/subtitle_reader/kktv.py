#coding=utf-8

from .subtitle_alg import SubtitleAlg
from .object_finder import find
from .compatible import role

class Kktv(SubtitleAlg):
	def getVideoPlayer(self):
		obj = self.main.focusObject
		videoPlayer = find(obj, 'parent', 'role', role('document'))
		return videoPlayer
	
	def getSubtitleContainer(self):
		return True
	
		videoPlayer = self.main.videoPlayer
		appName = videoPlayer.appModule.appName
		return getattr(self, appName + 'GetSubtitleContainer')()
	
	def getSubtitle(self):
		videoPlayer = self.main.videoPlayer
		appName = videoPlayer.appModule.appName
		return getattr(self, appName + 'GetSubtitle')()
	
	def chromeGetSubtitle(self):
		obj = self.main.videoPlayer
		obj = find(obj, 'firstChild', 'class', 'kktv-player__wrapper')
		if not obj:
			return
		obj = obj.next.next
		return super(Kktv, self).getSubtitle(obj)
	
	def firefoxGetSubtitle(self):
		obj = self.main.videoPlayer
		obj = obj.firstChild.firstChild.firstChild.next.next
		if 'subtitle' not in obj.IA2Attributes.get('class'):
			return ''
		
		return super(Kktv, self).getSubtitle(obj)
	
