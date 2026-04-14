#coding=utf-8

from . import SubtitleExtractor, SupportStatus
from ..object_finder import find
from ..compatible import role

class Bilibili(SubtitleExtractor):
	info = {
		'name': '哔哩哔哩',
		'url': 'https://www.bilibili.com/',
		'status': SupportStatus.supported,
	}
	windowTitle = '.+_哔哩哔哩_bilibili'
	def getVideoPlayer(self):
		obj = self.main.focusObject
		videoPlayer = find(obj, 'parent', 'class', 'bpx-player-primary-area')
		return videoPlayer
	
	def getSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		container = find(videoPlayer.firstChild.firstChild, 'next', 'class', 'bpx-player-subtitle')
		if not container:
			return
		
		return container.firstChild.firstChild
	
	
	def getSubtitle(self):
		obj = self.main.subtitleContainer
		return super(Bilibili, self).getSubtitle(obj)
	
