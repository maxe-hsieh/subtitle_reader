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
		videoPlayer = self.main.videoPlayer
		appName = videoPlayer.appModule.appName
		return getattr(self, appName + 'GetSubtitleContainer')()
	
	def chromeGetSubtitleContainer(self):
		obj = self.main.videoPlayer
		obj = obj.firstChild.firstChild.firstChild.firstChild.firstChild.next.next
		return obj
	
	def firefoxGetSubtitleContainer(self):
		obj = self.main.videoPlayer
		obj = find(obj, 'firstChild', 'role', role('grouping'))
		return obj
	
	def getSubtitle(self):
		obj = self.main.subtitleContainer
		return super(Kktv, self).getSubtitle(obj)
	
