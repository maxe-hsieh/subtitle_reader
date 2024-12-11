#coding=utf-8

from .subtitle_alg import SubtitleAlg
from .object_finder import find
from .compatible import role

class Bilibili(SubtitleAlg):
	def getVideoPlayer(self):
		obj = self.main.focusObject
		videoPlayer = find(obj, 'parent', 'class', 'bpx-player-primary-area')
		return videoPlayer
	
	def getSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		container = find(videoPlayer.firstChild.firstChild, 'next', 'class', 'bpx-player-subtitle-wrap')
		if not container:
			return
		
		return container.firstChild.firstChild
	
	
	def getSubtitle(self):
		obj = self.main.subtitleContainer
		return super(Bilibili, self).getSubtitle(obj)
	
