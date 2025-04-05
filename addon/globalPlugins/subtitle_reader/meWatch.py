#coding=utf-8

from .subtitle_alg import SubtitleAlg
from .object_finder import find
from .compatible import role

from logHandler import log

class MeWatch(SubtitleAlg):
	def getVideoPlayer(self):
		obj = self.main.focusObject
		videoPlayer = find(obj, 'parent', 'class', 'player', True)
		return videoPlayer
	
	def getSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		appName = videoPlayer.appModule.appName
		return getattr(self, appName + 'GetSubtitleContainer')()
	
	def chromeGetSubtitleContainer(self):
		container = self.main.videoPlayer
		container = container.firstChild.firstChild.next.firstChild.firstChild.next
		return container
	
	def firefoxGetSubtitleContainer(self):
		pass
	
	def getSubtitle(self):
		return super(MeWatch, self).getSubtitle()
	
