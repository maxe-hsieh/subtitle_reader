#coding=utf-8

from .subtitle_alg import SubtitleAlg
from .object_finder import find
from .compatible import role

class Iqy(SubtitleAlg):
	def getVideoPlayer(self):
		obj = self.main.focusObject
		treeInterceptor = obj.treeInterceptor
		if not treeInterceptor:
			return
		
		import textInfos
		info = treeInterceptor.makeTextInfo(textInfos.POSITION_CARET)
		if not info.find('play'):
			return
		
		videoPlayer = info._get_NVDAObjectAtStart()
		return videoPlayer
	
	def getSubtitleContainer(self):
		return True
	
	def getSubtitle(self):
		videoPlayer = self.main.videoPlayer
		appName = videoPlayer.appModule.appName
		return getattr(self, appName + 'GetSubtitle')(videoPlayer)
	
	def chromeGetSubtitle(self, obj):
		try:
			obj = obj.next.firstChild
		except:
			return ''
		
		obj = find(obj, 'next', 'class', 'iqp-subtitle')
		if not obj:
			return ''
		
		return super().getSubtitle(obj)
	
	def firefoxGetSubtitle(self):
		pass
	
