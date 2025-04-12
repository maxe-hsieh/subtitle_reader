#coding=utf-8

from .subtitle_alg import SubtitleAlg, SupportStatus
from .object_finder import find
from .compatible import role

from logHandler import log

class Netflix(SubtitleAlg):
	info = {
		'name': 'Netflix',
		'url': 'https://www.netflix.com/',
		'status': SupportStatus.supported,
	}
	def getVideoPlayer(self):
		obj = self.main.focusObject
		videoPlayer = find(obj, 'parent', 'role', role('dialog'))
		videoPlayer = videoPlayer or find(obj, 'parent', 'role', role('document'))
		
		return videoPlayer
	
	def getSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		appName = videoPlayer.appModule.appName
		return getattr(self, appName + 'GetSubtitleContainer')()
	
	def chromeGetSubtitleContainer(self):
		obj = self.main.videoPlayer
		# 有可能出現 toast 的狀況
		if find(obj, 'firstChild', 'id', 'toastRoot'):
			obj = obj.firstChild.firstChild.next
		
		obj = find(obj, 'firstChild', 'role', role('grouping'))
		return obj
	
	def firefoxGetSubtitleContainer(self):
		obj = self.main.videoPlayer
		# 有可能出現 toast 的狀況
		if find(obj, 'firstChild', 'id', 'toastRoot'):
			obj = obj.firstChild.next
		
		obj = find(obj, 'firstChild', 'role', role('grouping'))
		return obj
	
	def getSubtitle(self):
		
		obj = self.main.subtitleContainer
		obj = obj.next
		return super(Netflix, self).getSubtitle(obj)
	
