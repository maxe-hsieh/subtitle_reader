#coding=utf-8

from __future__ import unicode_literals

import os
import re

import ui
from logHandler import log

from .sound import play
from .config import conf
from .subtitle_alg import SubtitleAlg, SupportStatus
from .object_finder import find, search
from .compatible import role

class Twitch(SubtitleAlg):
	info = {
		'name': 'Twitch',
		'url': 'https://www.twitch.tv/',
		'status': SupportStatus.supported,
	}
	def __init__(self, *args, **kwargs):
		super(Twitch, self).__init__(*args, **kwargs)
		self.chatRoom = None
		self.chatContainer = None
		self.chatObject = None
		self.chatSender = ''
		self.chatSenderIsOwner = False
		self.chatSenderIsAdmin = ''
		self.chatSenderIsVerified = ''
		self.chat = ''
		self.chatContainerSearchObject = None
		self.chatBannerSearchObject = None
		self.chatSearchObject = None
	
	def getVideoPlayer(self):
		obj = self.main.focusObject
		return find(obj, 'parent', 'tag', 'main')
	
	def getSubtitleContainer(self):
		self.getChatContainer()
		return True
	
	def getChatContainer(self):
		obj = self.main.videoPlayer.next
		
		self.chatRoom = None
		self.chatContainer = None
		self.chatObject = None
		if self.chatContainerSearchObject:
			self.chatContainerSearchObject.cancel()
		
		self.chatContainerSearchObject = search(obj, lambda obj: obj.role == role('list'), self.onFoundChatContainer)
		
		if self.chatBannerSearchObject:
			self.chatBannerSearchObject.cancel()
		
		if self.chatSearchObject:
			self.chatSearchObject.cancel()
		
	
	def onFoundChatContainer(self, obj):
		self.chatContainer = obj
		#self.readChatBanner()
	
	def getSubtitle(self):
		return ''
	
	def onReadingSubtitle(self):
		self.readChat()
	
	
	def readChat(self):
		if not self.chatContainer:
			return
		
		if self.chatSearchObject and not self.chatSearchObject.isStopped:
			return
		
		self.chatObject = self.chatContainer.lastChild if not self.chatObject or not self.chatObject.role else self.chatObject
		nextChat = self.chatObject.next
		if nextChat is None:
			return
		
		self.chatObject = nextChat
		self.chatSender = ''
		self.chatSenderIsOwner = False
		self.chatSenderIsAdmin = ''
		self.chatSenderIsVerified = ''
		
		chat = self.chatObject.firstChild.next.firstChild
		chat = find(chat, 'next', 'name', ':')
		text = ''
		while chat:
			chat = chat.next
			text += getattr(chat, 'name', '')
		
		text = text.strip()
		if not text or text == self.chat:
			return
		
		self.chat = text
		ui.message(text)
	
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
		
	
