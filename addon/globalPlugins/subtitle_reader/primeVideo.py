#coding=utf-8

from .subtitle_alg import SubtitleAlg, SupportStatus
from .object_finder import find
from .compatible import role

class PrimeVideo(SubtitleAlg):
	info = {
		'name': 'Prime Video',
		'url': 'https://www.primevideo.com/',
		'status': SupportStatus.supported,
	}
	def getVideoPlayer(self):
		obj = self.main.focusObject
		appName = obj.appModule.appName
		videoPlayer = find(obj, 'parent', 'role', role('document'))
		videoPlayer = videoPlayer.firstChild
		if videoPlayer.IA2Attributes.get('class') != 'webPlayerSDKContainer':
			videoPlayer = videoPlayer.lastChild.firstChild
		
		return videoPlayer if videoPlayer.IA2Attributes.get('class') == 'webPlayerSDKContainer' else None
	
	def getSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		container = videoPlayer.lastChild.firstChild.firstChild.lastChild.previous.previous.firstChild.firstChild.firstChild
		return container
	
	def getSubtitle(self):
		obj = self.main.subtitleContainer
		obj = obj.next
		return super(PrimeVideo, self).getSubtitle(obj)
	
