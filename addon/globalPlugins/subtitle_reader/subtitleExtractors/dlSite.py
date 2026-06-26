#coding=utf-8

from . import SubtitleExtractor, SupportStatus
from ..object_finder import find
from ..compatible import role

from logHandler import log

class DlSite(SubtitleExtractor):
	info = {
		'name': 'DLsite',
		'url': 'https://www.dlsite.com/',
		'status': SupportStatus.supported,
	}
	windowTitle = '^DLsite Play'
	
	def getVideoPlayer(self):
		obj = self.main.focusObject
		# 由於點擊章節之後，焦點不會移至播放器，所以方便起見，我們不檢查播放器。
		return obj
	
	def getSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		appName = videoPlayer.appModule.appName
		return getattr(self, appName + 'GetSubtitleContainer')()
	
	def chromeGetSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		obj = find(videoPlayer, 'parent', 'role', role('document'))
		obj = obj.firstChild.firstChild.firstChild.lastChild
		obj = obj.firstChild.firstChild
		container = find(obj, 'next', 'class', 'textTrack')
		return container
	
	def firefoxGetSubtitleContainer(self):
		return self.chromeGetSubtitleContainer()
	
	def getSubtitle(self):
		obj = self.main.subtitleContainer
		return super(DlSite, self).getSubtitle(obj)
	
