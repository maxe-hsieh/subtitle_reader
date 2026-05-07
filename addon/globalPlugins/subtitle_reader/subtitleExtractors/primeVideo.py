#coding=utf-8

from . import SubtitleExtractor, SupportStatus
from ..object_finder import find
from ..compatible import role

class PrimeVideo(SubtitleExtractor):
	info = {
		'name': 'Prime Video',
		'url': 'https://www.primevideo.com/',
		'status': SupportStatus.supported,
	}
	windowTitle = '^Prime Video.+'
	def getVideoPlayer(self):
		obj = self.main.focusObject
		videoPlayer = find(obj, 'parent', 'id', 'dv-web-player')
		videoPlayer = videoPlayer.firstChild.firstChild.next
		return videoPlayer if 'player-container' in videoPlayer.IA2Attributes.get('class') else None
	
	def getSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		container = videoPlayer.firstChild.firstChild.next.next
		container = find(container, 'firstChild', 'class', 'atvwebplayersdk-persistent-component-container')
		return container
	
	def getSubtitle(self):
		obj = self.main.subtitleContainer
		obj = obj.next
		return super(PrimeVideo, self).getSubtitle(obj)
	
