#coding=utf-8

from .subtitle_alg import SubtitleAlg, SupportStatus
from .object_finder import find
from .compatible import role

from logHandler import log

class HboMax(SubtitleAlg):
	info = {
		'name': 'HBO Max',
		'url': 'https://play.hbomax.com/',
		'status': SupportStatus.supported,
	}
	def getVideoPlayer(self):
		obj = self.main.focusObject
		videoPlayer = find(obj, 'parent', 'role', role('document'))
		# 全螢幕的影片播放器
		if find(videoPlayer, 'firstChild', 'role', role('grouping')):
			return videoPlayer
		
		videoPlayer = find(videoPlayer, 'firstChild', 'id', 'app-root')
		if not videoPlayer:
			return
		
		videoPlayer = find(videoPlayer.firstChild, 'next', 'id', 'layer-root-player-screen')
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
		return super(HboMax, self).getSubtitle(obj)
	
