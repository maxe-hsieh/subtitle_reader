#coding=utf-8

from .compatible import role

class SubtitleAlg(object):
	def __init__(self, main):
		self.main = main
	
	def getVideoPlayer(self):
		raise NotImplementedError
	
	def getSubtitleContainer(self):
		raise NotImplementedError
	
	def msedgeGetSubtitleContainer(self):
		# Edge 取得字幕容器的方式，通常與 Chrome 相同，故實做一個通用方法。
		return self.chromeGetSubtitleContainer()
	
	def braveGetSubtitleContainer(self):
		# Brave 取得字幕容器的方法也與 Chrome 相同。
		return self.chromeGetSubtitleContainer()
	
	def getSubtitle(self, obj=None):
		subtitle = ''
		if obj is None:
			obj = self.main.subtitleContainer
		
		while obj and not obj.name:
			try:
				obj = obj.firstChild
			except:
				obj = None
			
		
		pobj = obj
		while obj:
			if obj.name:
				subtitle += obj.name + '\r\n'
			
			pobj = obj
			obj = obj.next
		
		if pobj.role == role('unknown'):
			return
		
		return subtitle
	
