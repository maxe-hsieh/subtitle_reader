#coding=utf-8

from .subtitle_alg import SubtitleAlg
from .object_finder import find
from .compatible import role

class PrimeVideo(SubtitleAlg):
	def getVideoPlayer(self):
		obj = self.main.focusObject
		appName = obj.appModule.appName
		videoPlayer = find(obj, 'parent', 'class', 'atvwebplayersdk-overlays-container fpqiyer')
		if videoPlayer:
			videoPlayer = obj.parent.parent.parent.parent
		
		return videoPlayer
	
	def getSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		container = videoPlayer.next.firstChild.firstChild
		return container
	
	def getSubtitle(self):
		obj = self.main.subtitleContainer
		return super(PrimeVideo, self).getSubtitle(obj)
	
