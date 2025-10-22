#coding=utf-8

from __future__ import unicode_literals

from .compatible import role

class SubtitleAlg(object):
	# 未來將改為 SubtitleProvider
	'''
	影音平台資訊：
		- name: 影音平台名稱
		- url: 影音平台網址
		- status: 影音平台狀態
	'''
	info = {}
	
	# 使用視窗標題或者網址，判斷焦點是否位於影音平台（方法二選一）。
	windowTitle = None
	url = None
	
	def __init__(self, main, onFoundSubtitle=None):
		self.main = main
		if not onFoundSubtitle:
			onFoundSubtitle = main.processSubtitle
		
		self.onFoundSubtitle = onFoundSubtitle
		self.searchingSubtitle = False
	
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
	
	def onReadingSubtitle(self):
		pass
	
	def msedgeGetSubtitle(self, obj):
		return self.chromeGetSubtitle(obj)
	
	def braveGetSubtitle(self, obj):
		return self.chromeGetSubtitle(obj)
	
	# Yandex 瀏覽器
	def browserGetSubtitle(self, obj):
		return self.chromeGetSubtitle(obj)
	
	def getSubtitle(self, obj=None):
		subtitle = ''
		if obj is None:
			obj = self.main.subtitleContainer
		
		while obj and not obj.name:
			obj = obj.firstChild
		
		pobj = obj
		while obj:
			if obj.name:
				subtitle += obj.name + ' | \r\n'
			
			pobj = obj
			obj = obj.next
		
		if not pobj or pobj.role == role('unknown'):
			return
		
		return subtitle
	

# 平台支援狀態
class SupportStatus(object):
	invalid = _('失效')
	supported = _('正常')
