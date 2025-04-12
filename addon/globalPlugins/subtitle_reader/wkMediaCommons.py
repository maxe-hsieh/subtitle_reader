#coding=utf-8

from .subtitle_alg import SubtitleAlg, SupportStatus
from .object_finder import find
from .compatible import role

class WKMediaCommons(SubtitleAlg):
	info = {
		'name': 'WKMediaCommons',
		'url': 'https://commons.wikimedia.org/',
		'status': SupportStatus.supported,
	}
	def getVideoPlayer(self):
		obj = self.main.focusObject
		return find(obj, 'parent', 'id', 'mwe_player_0')
	
	def getSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		appName = videoPlayer.appModule.appName
		return getattr(self, appName + 'GetSubtitleContainer')()
	
	def chromeGetSubtitleContainer(self):
		obj = self.main.videoPlayer
		obj = obj.firstChild
		return find(obj, 'next', 'class', 'vjs-text-track-display')
	
	def firefoxGetSubtitleContainer(self):
		return self.chromeGetSubtitleContainer()
	
