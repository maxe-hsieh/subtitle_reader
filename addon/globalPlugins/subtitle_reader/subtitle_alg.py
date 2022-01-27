#coding=utf-8

class SubtitleAlg(object):
	def __init__(self, main):
		self.main = main
	
	def getVideoPlayer(self):
		raise NotImplementedError
	
	def getSubtitleContainer(self):
		raise NotImplementedError
	
	def msedgeGetSubtitleContainer(self):
		# Edge 取得字幕的方式，通常與 Chrome 相同，故實做一個通用方法。
		return self.chromeGetSubtitleContainer()
	
	def getSubtitle(self):
		subtitle = ''
		obj = self.main.subtitleContainer
		while obj and not obj.name:
			try:
				obj = obj.firstChild
			except:
				obj = None
			
		
		while obj:
			if obj.name:
				subtitle += obj.name + '\r\n'
			
			obj = obj.next
		
		return subtitle
	
