#coding=utf-8

import os
import re

import ui
from logHandler import log

from .sound import play
from .config import conf
from .subtitle_alg import SubtitleAlg
from .object_finder import find, search
from .compatible import role

class Youtube(SubtitleAlg):
	def __init__(self, *args, **kwargs):
		super(Youtube, self).__init__(*args, **kwargs)
		self.chapter = ''
		self.ce = str() # 資訊卡
		self.chatContainer = None
		self.chatObject = None
		self.chatSender = ''
		self.chat = ''
		self.searchObject = None
		self.chatSearchObject = None
	
	def getVideoPlayer(self):
		'''
		根據元件 id 找出 Youtube 影片撥放器
		'''
		obj = self.main.focusObject
		videoPlayer = find(obj, 'parent', 'id', ['movie_player', 'c4-player', 'player-container'])
		if videoPlayer:
			self.chatContainer = None
			if videoPlayer.IA2Attributes.get('id') == 'player-container':
				videoPlayer = videoPlayer.firstChild.firstChild.firstChild
			
		
		return videoPlayer
	
	def getSubtitleContainer(self):
		self.getChatContainer()
		
		# 由於 Youtube 的字幕容器是不停變動的，所以改為在每次取得字幕時一併取得容器，在此方法回傳 True 作為假的字幕容器。
		return True
	
	def getChatContainer(self):
		if not conf['readChat']:
			return
		
		try:
			obj = next(self.main.videoPlayer.treeInterceptor._iterNodesByType('frame')).obj
		except:
			obj = None
		
		self.chatContainer = None
		self.chatObject = None
		search(obj, lambda obj: 'yt-live-chat-item-list-renderer' in obj.IA2Attributes.get('class') and obj.IA2Attributes.get('id') == 'items', self.onFoundChatContainer).name = 'chat container'
		
	
	def onFoundChatContainer(self, obj):
		self.chatContainer = obj
	
	def getSubtitle(self):
		'''
		取得字幕
		'''
		self.readChapter()
		
		self.promptInfoCard()
		
		self.get_subtitle_object()
		
		self.readChat()
	
	def get_subtitle_object(self):
		'''
		根據元件 id 從 Youtube 影片撥放器找出第一個字幕元件
		'''
		obj = self.main.videoPlayer.firstChild
		obj = find(obj, 'next', 'id', 'ytp-caption-window-container')
		if not obj:
			return self.onNotFoundSubtitleObject()
		
		self.onFoundSubtitleObject(obj)
	
	def onNotFoundSubtitleObject(self):
		pass
	
	def onFoundSubtitleObject(self, obj):
		subtitle = str()
		# 根據瀏覽器，分別處理取得字幕的方式。
		browser = obj.appModule.appName
		subtitle = getattr(self, browser + 'GetSubtitle')(obj)
		if not subtitle is None:
			return self.onFoundSubtitle(subtitle)
		
	
	def chromeGetSubtitle(self, obj):
		subtitle = ''
		line = getattr(obj, 'firstChild', None)
		
		# 變例每一行字幕
		while line is not None:
			part = line.firstChild
			
			# 處理一行當中被切成多個部分的字幕
			while part is not None:
				# Youtube 改版，在 chromium 有時候字幕會出現在當前物件，有時會出現在他的後代。
				# 屬性 name 沒有文字時會回傳 None 而非空字串
				text = getattr(part, 'name', '') or str()
				child = getattr(part, 'firstChild', '')
				text += getattr(child, 'name', '') or str()
				text = text.replace(u'​', '').strip()
				if text:
					subtitle += text + ' | '
				
				part = part.next
			
			if subtitle:
				subtitle += '\r\n'
			
			line = line.next
		
		return subtitle
	
	def firefoxGetSubtitle(self, obj):
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
	
	def msedgeGetSubtitle(self, obj):
		return self.chromeGetSubtitle(obj)
	
	def braveGetSubtitle(self, obj):
		return self.chromeGetSubtitle(obj)
	
	def promptInfoCard(self):
		if not conf['infoCardPrompt']:
			return
		
		ce = None
		try:
			ce = self.get_ce()
		except Exception as e:
			pass
		
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
			class_name = obj.IA2Attributes.get('class', '')
			if 'ytp-ce' in class_name and 'ytp-ce-shadow' not in class_name:
				ce += 'ce\n'
			elif ce:
				break
			obj = obj.next
		return ce
	
	def readChapter(self):
		if not conf['readChapter']:
			return
		
		text = ''
		try:
			text = self.getChapter()
		except Exception as e:
			pass
		
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
		
		text = obj.firstChild.value
		text = re.sub(u'\\d+.+$', '', text)
		return text
	
	def readChat(self):
		if not self.chatContainer:
			return
		
		if self.chatSearchObject and not self.chatSearchObject.isStopped:
			return
		
		self.chatObject = self.chatContainer.lastChild if not self.chatObject or not self.chatObject.role else self.chatObject.next
		if self.chatObject is None:
			return
		
		self.chatSender = ''
		self.chatSearchObject = search(self.chatObject.firstChild, self.chatCondition, self.onFoundChatObject, continueOnFound=True)
	
	def chatCondition(self, obj):
		if 'ytd-sponsorships-live-chat-gift-redemption-announcement-renderer' in obj.IA2Attributes.get('class'):
			return
		
		matchIds = [
			'message',
		]
		
		if conf['readChatGiftSponser']:
			matchIds.append('primary-text')
		
		if conf['readChatSender']:
			matchIds.append('author-name')
		
		return obj.IA2Attributes.get('id') in matchIds
	
	def onFoundChatObject(self, chat):
		id = chat.IA2Attributes.get('id')
		if id == 'author-name':
			name = chat.firstChild.name
			self.chatSender = name if name else ''
			return
		
		self.chatSearchObject.cancel()
		
		chat = getattr(chat, 'firstChild', None)
		if not chat:
			return
		
		text = ''
		loopingChat = chat
		while loopingChat:
			chat = loopingChat
			loopingChat = loopingChat.next
			if conf['omitChatGraphic'] and chat.role == role('graphic'):
				continue
			
			text += chat.name if chat.name else ''
			
		
		text = text.strip()
		if not text:
			return
		
		if text == self.chat:
			return
		
		self.chat = text
		if conf['readChatSender']:
			ui.message(self.chatSender)
		
		ui.message(text)
		
	
