#coding=utf-8

from .subtitle_alg import SubtitleAlg, SupportStatus
from .object_finder import find
from .compatible import role

class DisneyPlus(SubtitleAlg):
	info = {
		'name': 'Disney+',
		'url': 'https://www.disneyplus.com/',
		'status': SupportStatus.supported,
	}
	def getVideoPlayer(self):
		obj = self.main.focusObject
		videoPlayer = find(obj, 'parent', 'class', 'btm-media-clients')
		return videoPlayer
	
	def getSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		appName = videoPlayer.appModule.appName
		return getattr(self, appName + 'GetSubtitleContainer')()
	
	def chromeGetSubtitleContainer(self):
		obj = self.main.videoPlayer
		obj = find(obj, 'firstChild', 'role', role('GROUPING'))
		if not obj:
			return
		
		container = obj.next
		return container
	
	def firefoxGetSubtitleContainer(self):
		return self.chromeGetSubtitleContainer()
	
