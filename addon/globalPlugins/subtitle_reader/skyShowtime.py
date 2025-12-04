#coding=utf-8

from .subtitle_alg import SubtitleAlg, SupportStatus
from .object_finder import find
from .compatible import role

from logHandler import log

class SkyShowtime(SubtitleAlg):
	info = {
		'name': 'SkyShowtime',
		'url': 'https://www.skyshowtime.com/',
		'status': SupportStatus.supported,
	}
	def getVideoPlayer(self):
		obj = self.main.focusObject
		videoPlayer = find(obj, 'parent', 'class', 'playback-overlay__container vod')
		return videoPlayer
	
	def getSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		appName = videoPlayer.appModule.appName
		return getattr(self, appName + 'GetSubtitleContainer')()
	
	def chromeGetSubtitleContainer(self):
		obj = self.main.videoPlayer.next
		obj = find(obj, 'firstChild', 'role', role('grouping'))
		return obj
	
	def firefoxGetSubtitleContainer(self):
		return
	
	def getSubtitle(self):
		obj = self.main.subtitleContainer
		obj = obj.next
		return super(SkyShowtime, self).getSubtitle(obj)
	
