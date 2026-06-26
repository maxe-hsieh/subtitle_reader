#coding=utf-8

from . import SubtitleExtractor, SupportStatus
import textInfos

from logHandler import log

class AsmrOnline(SubtitleExtractor):
	info = {
		'name': 'ASMR Online',
		'url': 'https://www.asmr.one/',
		'status': SupportStatus.supported,
	}
	windowTitle = 'RJ\\d+ .+ - ASMR Online'
	
	def getVideoPlayer(self):
		obj = self.main.focusObject
		# 由於點擊章節之後，焦點不會移至播放器，且字幕位置也不再播放器附近，所以方便起見，我們不檢查播放器。
		return obj
	
	def getSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		appName = videoPlayer.appModule.appName
		return getattr(self, appName + 'GetSubtitleContainer')()
	
	def chromeGetSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		textInfo = videoPlayer.treeInterceptor.makeTextInfo(textInfos.POSITION_LAST)
		textInfo.move(textInfos.UNIT_CHARACTER, -1)
		container = textInfo.NVDAObjectAtStart
		if 'lyric' in container.IA2Attributes.get('id'):
			return container
		
		return None
	
	def firefoxGetSubtitleContainer(self):
		return self.chromeGetSubtitleContainer()
	
	def getSubtitle(self):
		obj = self.main.subtitleContainer
		return super(AsmrOnline, self).getSubtitle(obj)
	
