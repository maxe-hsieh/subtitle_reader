#coding=utf-8

from __future__ import unicode_literals

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
		self.ce = str() # 資訊卡
		self.chatRoom = None
		self.chatContainer = None
		self.chatObject = None
		self.chatSender = ''
		self.chatSenderIsOwner = False
		self.chatSenderIsAdmin = ''
		self.chatSenderIsVerified = ''
		self.chat = ''
		self.voting = False
		self.chatContainerSearchObject = None
		self.chatBannerSearchObject = None
		self.chatSearchObject = None
	
	def getVideoPlayer(self):
		'''
		根據元件 id 找出 Youtube 影片撥放器
		'''
		obj = self.main.focusObject
		videoPlayer = find(obj, 'parent', 'id', ['movie_player', 'c4-player', 'player-container'])
		if videoPlayer:
			if videoPlayer.IA2Attributes.get('id') == 'player-container':
				videoPlayer = videoPlayer.firstChild.firstChild.firstChild
			
		
		return videoPlayer
	
	def getSubtitleContainer(self):
		self.getChatContainer()
		
		videoPlayer = self.main.videoPlayer
		# 沉浸式翻譯
		container = find(videoPlayer.firstChild, 'next', 'id', 'immersive-translate-caption-window')
		# Youtube
		container = container or find(videoPlayer.firstChild, 'next', 'id', 'ytp-caption-window-container')
		if not container:
			# 為了聊天室需要不斷執行，還是回傳 True
			return True
		
		return container
	
	def getChatContainer(self):
		if not conf['readChat']:
			return
		
		try:
			obj = next(self.main.videoPlayer.treeInterceptor._iterNodesByType('frame')).obj
		except:
			obj = None
		
		self.chatRoom = None
		self.chatContainer = None
		self.chatObject = None
		self.voting = None
		if self.chatContainerSearchObject:
			self.chatContainerSearchObject.cancel()
		
		self.chatContainerSearchObject = search(obj, lambda obj: ('yt-live-chat-item-list-renderer' in obj.IA2Attributes.get('class') and obj.IA2Attributes.get('id') == 'items') or obj.IA2Attributes.get('id') == 'chat', self.onFoundChatContainer, continueOnFound=True)
		
		if self.chatBannerSearchObject:
			self.chatBannerSearchObject.cancel()
		
		if self.chatSearchObject:
			self.chatSearchObject.cancel()
		
	
	def onFoundChatContainer(self, obj):
		id = obj.IA2Attributes.get('id')
		if id == 'chat':
			self.chatRoom = obj
		elif id == 'items':
			self.chatContainer = obj
			self.chatContainerSearchObject.cancel()
			self.readChatBanner()
		
	
	def getSubtitle(self):
		'''
		取得字幕
		'''
		self.promptInfoCard()
		
		subtitle = str()
		container = self.main.subtitleContainer
		if container is True:
			# 表示沒有字幕容器
			return
		
		# 根據瀏覽器，分別處理取得字幕的方式。
		browser = container.appModule.appName
		subtitle = getattr(self, browser + 'GetSubtitle')(container)
		return subtitle
	
	def onReadingSubtitle(self):
		self.readVoting()
		self.readChat()
	
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
	
	def readChat(self):
		if not self.chatContainer:
			return
		
		if self.chatSearchObject and not self.chatSearchObject.isStopped:
			return
		
		self.chatObject = self.chatContainer.lastChild if not self.chatObject or not self.chatObject.role else self.chatObject.next
		if self.chatObject is None:
			return
		
		self.chatSender = ''
		self.chatSenderIsOwner = False
		self.chatSenderIsAdmin = ''
		self.chatSenderIsVerified = ''
		
		self.chatSearchObject = search(self.chatObject.firstChild, self.chatCondition, self.onFoundChatObject, continueOnFound=True)
	
	def chatCondition(self, obj):
		if 'ytd-sponsorships-live-chat-gift-redemption-announcement-renderer' in obj.IA2Attributes.get('class'):
			return
		
		matchIds = [
			'message',
			'primary-text',
			'author-name',
			'chat-badges',
		]
		
		return obj.IA2Attributes.get('id') in matchIds
	
	def onFoundChatObject(self, chat):
		id = chat.IA2Attributes.get('id')
		if id == 'author-name':
			name = chat.firstChild.name
			self.chatSender = name if name else ''
			self.chatSenderIsOwner = 'owner' in chat.IA2Attributes.get('class', '')
			verified = chat.firstChild.next
			if verified:
				self.chatSenderIsVerified = verified.firstChild.name
			
			return
		
		if id == 'chat-badges':
			if chat.childCount >= 2 or chat.firstChild.firstChild.firstChild.role != role('GRAPHIC'):
				name = chat.firstChild.name
				self.chatSenderIsAdmin = name if name else ''
			
			return
		
		self.chatSearchObject.cancel()
		
		if conf['onlyReadManagersChat'] and not self.chatSenderIsOwner and not self.chatSenderIsAdmin:
			return
		
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
		
		sender = '{name}。\r\n{isVerified}。\r\n{isAdmin}。\r\n'.format(name=self.chatSender, isVerified=self.chatSenderIsVerified, isAdmin=self.chatSenderIsAdmin)
		if conf['readChatSender'] or self.chatSenderIsOwner or self.chatSenderIsVerified or self.chatSenderIsAdmin:
			text = sender + text
		
		ui.message(text)
		
	
	def readChatBanner(self):
		if not self.chatContainer:
			return
		
		obj = self.chatContainer.parent.previous
		banner = None
		while obj:
			banner = find(obj, 'firstChild', 'id', 'banner-container')
			if banner:
				break
			
			obj = obj.previous
		
		if not banner:
			return
		
		self.chatBannerSearchObject = search(banner, lambda obj: bool(obj.name) and obj.role != role('LINK'), lambda banner: ui.message(banner.name if banner.role != role('BUTTON') else '聊天室橫幅'), continueOnFound=True)
	
	def readVoting(self):
		if not self.chatRoom:
			return
		
		votingObj = self.chatRoom.lastChild
		votingObj = find(votingObj, 'firstChild', 'class', 'style-scope yt-live-chat-poll-renderer')
		if bool(votingObj) != self.voting:
			self.voting = bool(votingObj)
			if self.voting:
				ui.message(_('意見調查：'))
				search(votingObj, lambda obj: True, self.onSearchVoting, continueOnFound=True)
			
		
	
	def onSearchVoting(self, obj):
		msg = getattr(obj, 'name', '') or ''
		# 掠過有 id 或 name 為  • 的原件
		if msg == ' • ' or obj.IA2Attributes.get('id'):
			return
		
		if msg:
			ui.message(msg)
		
	
