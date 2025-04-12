#coding=utf-8

from __future__ import unicode_literals

from .subtitle_alg import SubtitleAlg, SupportStatus
from .object_finder import find
from .compatible import role

from logHandler import log

class MarumaruX(SubtitleAlg):
	info = {
		'name': '唱歌學日語',
		'url': 'https://www.marumaru-x.com/japanese-song',
		'status': SupportStatus.supported,
	}
	def getVideoPlayer(self):
		obj = self.main.focusObject
		videoPlayer = find(obj, 'parent', 'id', 'player')
		# 有可能找到 YT 的，跳過它。
		if videoPlayer and not videoPlayer.next:
			videoPlayer = find(videoPlayer.parent, 'parent', 'id', 'player')
		
		return videoPlayer
	
	def getSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		appName = videoPlayer.appModule.appName
		return getattr(self, appName + 'GetSubtitleContainer')()
	
	def chromeGetSubtitleContainer(self):
		player = self.main.videoPlayer
		container = player.next.firstChild.next
		return container
	
	def firefoxGetSubtitleContainer(self):
		pass
	
	def getSubtitle(self):
		return super(MarumaruX, self).getSubtitle()
	
