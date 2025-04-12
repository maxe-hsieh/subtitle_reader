#coding=utf-8

from .subtitle_alg import SubtitleAlg, SupportStatus
from .object_finder import find
from .compatible import role

from logHandler import log

class AppleTVPlus(SubtitleAlg):
	info = {
		'name': 'Apple TV+',
		'url': 'https://tv.apple.com/',
		'status': SupportStatus.supported,
	}
	def getVideoPlayer(self):
		obj = self.main.focusObject
		videoPlayer = find(obj, 'parent', 'role', role('dialog'))
		
		return videoPlayer
	
	def getSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		appName = videoPlayer.appModule.appName
		return getattr(self, appName + 'GetSubtitleContainer')()
	
	def chromeGetSubtitleContainer(self):
		obj = self.main.videoPlayer
		try:
			obj = obj.firstChild.firstChild.lastChild
		except:
			log.debug('Subtitle container not found.')
		
		return obj
	
	def firefoxGetSubtitleContainer(self):
		obj = self.main.videoPlayer
		obj = find(obj, 'firstChild', 'role', role('grouping'))
		return obj
	
	def getSubtitle(self):
		obj = self.main.subtitleContainer
		appName = obj.appModule.appName
		if appName == 'firefox':
			obj = obj.next
			if not obj:
				return ''
			
		
		return super(AppleTVPlus, self).getSubtitle(obj)
	
