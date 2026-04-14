#coding=utf-8

from . import SubtitleExtractor, SupportStatus
from ..object_finder import find
from ..compatible import role

from logHandler import log

class Netflix(SubtitleExtractor):
	info = {
		'name': 'Netflix',
		'url': 'https://www.netflix.com/',
		'status': SupportStatus.supported,
	}
	windowTitle = '.*?Netflix'
	def getVideoPlayer(self):
		obj = self.main.focusObject
		videoPlayer = find(obj, 'parent', 'role', role('dialog')) or find(obj, 'parent', 'class', 'player')
		
		return videoPlayer
	
	def getSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		appName = videoPlayer.appModule.appName
		return getattr(self, appName + 'GetSubtitleContainer')()
	
	def chromeGetSubtitleContainer(self):
		obj = self.main.videoPlayer
		obj = find(obj, 'firstChild', 'role', role('grouping'))
		return obj
	
	def firefoxGetSubtitleContainer(self):
		obj = self.main.videoPlayer
		obj = find(obj, 'firstChild', 'role', role('grouping'))
		return obj
	
	def getSubtitle(self):
		
		obj = self.main.subtitleContainer
		obj = obj.next
		return super(Netflix, self).getSubtitle(obj)
	
