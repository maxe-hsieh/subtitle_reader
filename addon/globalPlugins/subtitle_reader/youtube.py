#coding=utf-8

import os
import re
from .sound import play
from .config import conf
from .subtitle_alg import SubtitleAlg
from .object_finder import find

class Youtube(SubtitleAlg):
	def __init__(self, *args, **kwargs):
		super(Youtube, self).__init__(*args, **kwargs)
		self.chapter = ''
		self.ce = str() # 資訊卡
	
	def getVideoPlayer(self):
		'''
		根據元件 id 找出 Youtube 影片撥放器
		'''
		obj = self.main.focusObject
		return find(obj, 'parent', 'id', ['movie_player', 'c4-player'])
	
	def getSubtitleContainer(self):
		# 由於 Youtube 的字幕容器是不停變動的，所以改為在每次取得字幕時一併取得容器，在此方法回傳 True 作為假的字幕容器。
		return True
	
	def getSubtitle(self):
		'''
		取得字幕
		'''
		self.speakChapter()
		
		self.promptInfoCard()
		
		subtitle = str()
		# 根據瀏覽器，分別處理取得字幕的方式。
		browser = self.main.videoPlayer.appModule.appName
		subtitle = getattr(self, browser + 'GetSubtitle')()
		return subtitle
	
	def get_subtitle_object(self):
		'''
		根據元件 id 從 Youtube 影片撥放器找出第一個字幕元件
		'''
		obj = self.main.videoPlayer.firstChild
		while obj:
			try:
				if 'caption-window-' in str(obj.IA2Attributes.get('id')):
					return obj
				
			except AttributeError:
				pass
			
			obj = obj.next
		
	
	def chromeGetSubtitle(self):
		obj = self.get_subtitle_object()
		if not obj:
			return ''
		
		subtitle = ''
		
		line = getattr(obj, 'firstChild', None)
		# 變例每一行字幕
		while line is not None:
			part = line.firstChild
			# 處理一行當中被切成多個部分的字幕
			while part is not None:
				text = getattr(part, 'name', '')
				if isinstance(text, str):
					text = text.strip()
				
				if text:
					subtitle += text + '\r\n'
				
				part = part.next
			
			line = line.next
		
		return subtitle
	
	def firefoxGetSubtitle(self):
		obj = self.get_subtitle_object()
		if not obj:
			return ''
		
		subtitle = ''
		obj = obj.firstChild
		while obj is not None and 'caption-window-' in str(obj.IA2Attributes.get('id')):
			try:
				# 取得多行字幕
				char_obj = obj.firstChild.firstChild
				for i in range(char_obj.parent.childCount):
					# 處理一個元素只放一個字的狀況
					subtitle += char_obj.firstChild.firstChild.name + '\r\n'
					
					char_obj = char_obj.next
				
				obj = obj.next
			
			except:
				return
			
		
		return subtitle
	
	def msedgeGetSubtitle(self):
		return self.chromeGetSubtitle()
	
	def braveGetSubtitle(self):
		return self.chromeGetSubtitle()
	
	def promptInfoCard(self):
		if not conf['infoCardPrompt']:
			return
		
		ce = self.get_ce()
		if ce is None:
			return
		
		if ce != self.ce and self.ce in ce:
			# 當資訊卡內容增加時才播放音效
			play(os.path.dirname(__file__) + r'\sounds\ce.ogg')
		
		self.ce = ce
	
	def get_ce(self):
		'''
		取得資訊卡
		'''
		if not self.main.videoPlayer:
			return
		
		ce = ''
		obj = self.main.videoPlayer.firstChild
		while obj:
			class_name = obj.IA2Attributes.get('class')
			if 'ytp-ce' in class_name and 'ytp-ce-shadow' not in class_name:
				ce += 'ce\n'
			elif ce:
				break
			obj = obj.next
		return ce
	
	def speakChapter(self):
		text = self.getChapter()
		if not text:
			return
		
		if text == self.chapter:
			return
		
		self.chapter = text
		ui.message(text)
	
	def getChapter(self):
		obj = self.main.videoPlayer.lastChild.firstChild
		if not obj or obj.IA2Attributes.get('class') != 'ytp-progress-bar-container':
			return ''
		
		text = obj.firstChild.next.value
		text = re.sub(u' ?(\\d+ 天 )?(\\d+ 小時 )?(\\d+ 分鐘 )?\\d+ 秒，共 (\\d+ 天 )?(\\d+ 小時 )?(\\d+ 分鐘 )?\\d+ 秒$', '', text)
		return text
	
