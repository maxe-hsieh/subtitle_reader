#coding=utf-8

# 字幕閱讀器
# 作者：福恩 <maxe@mail.batol.net>


import re
import webbrowser
import ui
import time

import addonHandler
addonHandler.initTranslation()

import globalPluginHandler
import api
from globalVars import appArgs
from logHandler import log
from comtypes import COMError
from . import sound
from . import gui
from .config import conf

from .subtitleExtractors import SubtitleExtractor
SubtitleExtractor.initialize()

from .potPlayer import PotPlayer
from .update import Update

nvdaGui = gui.gui


wx = gui.wx

conf.load(appArgs.configPath + r'\subtitle_reader.json')

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	# Translators: Script category for Subtitle Reader
	scriptCategory = _(u'字幕閱讀器')
	def __new__(cls):
		# 在安全桌面不執行字幕閱讀器
		if cls.isRunningOnSecureDesktop():
			# 傳回附加元件的基礎類別實體，表示沒有任何功能的附加元件。
			return globalPluginHandler.GlobalPlugin()
		
		return super(cls, cls).__new__(cls)
	
	def __init__(self, *args, **kwargs):
		super(GlobalPlugin, self).__init__(*args, **kwargs)
		
		self.subtitleExtractor = None
		self.supportedBrowserAppNames = ('chrome', 'brave', 'firefox', 'msedge', 'browser') # browser = Yandex
		self.focusObject = None
		self.urlObjects = {}
		self.videoPlayer = None
		self.subtitleContainer = None
		self.subtitle = str()
		self.emptySubtitleTime = 0
		# 使用 wx.PyTimer 不斷執行函數
		self.readSubtitleTimer = nvdaGui.NonReEntrantTimer(self.readSubtitle)
		self.startReadSubtitleTime = 0
		
		sound.init()
		
		self.update = Update()
		# 初始化選單
		self.initMenu()
		self.potPlayer = PotPlayer()
	
	def initMenu(self):
		menu = self.menu = gui.Menu(self)
		gui.tray.Bind(gui.wx.EVT_MENU, self.script_toggleSwitch, menu.switch)
		gui.tray.Bind(gui.wx.EVT_MENU, self.toggleBackgroundReading, menu.backgroundReading)
		gui.tray.Bind(gui.wx.EVT_MENU, self.toggleReadChat, menu.readChat)
		gui.tray.Bind(gui.wx.EVT_MENU, self.toggleReadChatSender, menu.readChatSender)
		gui.tray.Bind(gui.wx.EVT_MENU, self.toggleOnlyReadManagersChat, menu.onlyReadManagersChat)
		gui.tray.Bind(gui.wx.EVT_MENU, self.toggleReadChatGiftSponser, menu.readChatGiftSponser)
		gui.tray.Bind(gui.wx.EVT_MENU, self.toggleOmitChatGraphic, menu.omitChatGraphic)
		gui.tray.Bind(gui.wx.EVT_MENU, self.toggleInfoCardPrompt, menu.infoCardPrompt)
		gui.tray.Bind(gui.wx.EVT_MENU, self.update.manualCheck, menu.checkForUpdate)
		gui.tray.Bind(gui.wx.EVT_MENU, self.update.openCurrentChangeLog, menu.openCurrentChangeLog)
		gui.tray.Bind(gui.wx.EVT_MENU, self.update.openLatestChangeLog, menu.openLatestChangeLog)
		gui.tray.Bind(gui.wx.EVT_MENU, self.update.toggleCheckAutomatic, menu.checkUpdateAutomatic)
		menu.crunchyrollTM.Bind(gui.wx.EVT_MENU, self.onCrunchyrollTMChrome, menu.crunchyrollTMChrome)
		menu.crunchyrollTM.Bind(gui.wx.EVT_MENU, self.onCrunchyrollTMFirefox, menu.crunchyrollTMFirefox)
		menu.crunchyrollTM.Bind(gui.wx.EVT_MENU, self.onCrunchyrollTMEdge, menu.crunchyrollTMEdge)
		menu.crunchyrollSetup.Bind(gui.wx.EVT_MENU, self.onCrunchyrollInstallScript, menu.crunchyrollInstallScript)
		menu.crunchyrollSetup.Bind(gui.wx.EVT_MENU, self.onCrunchyrollHelp, menu.crunchyrollHelp)
		# 聯絡開發者
		menu.contactDeveloper.Bind(gui.wx.EVT_MENU, self.contactUseWhatsApp, menu.contactUseWhatsApp)
		menu.contactDeveloper.Bind(gui.wx.EVT_MENU, self.contactUseFacebook, menu.contactUseFacebook)
		menu.contactDeveloper.Bind(gui.wx.EVT_MENU, self.contactUseQq, menu.contactUseQq)
		menu.contactDeveloper.Bind(gui.wx.EVT_MENU, self.contactUseLine, menu.contactUseLine)
		menu.contactDeveloper.Bind(gui.wx.EVT_MENU, self.contactUseDiscord, menu.contactUseDiscord)
		menu.contactDeveloper.Bind(gui.wx.EVT_MENU, self.contactUseX, menu.contactUseX)
		
		# 支援的影音平台
		for item in menu.platforms.GetMenuItems():
			menu.platforms.Bind(gui.wx.EVT_MENU, self.openPlatformPage, item)
		
		menu.switch.Check(conf['switch'])
		menu.backgroundReading.Check(conf['backgroundReading'])
		menu.readChat.Check(conf['readChat'])
		menu.readChatSender.Check(conf['readChatSender'])
		menu.onlyReadManagersChat.Check(conf['onlyReadManagersChat'])
		menu.readChatGiftSponser.Check(conf['readChatGiftSponser'])
		menu.omitChatGraphic.Check(conf['omitChatGraphic'])
		menu.infoCardPrompt.Check(conf['infoCardPrompt'])
		menu.checkUpdateAutomatic.Check(conf['checkUpdateAutomatic'])
	
	def terminate(self):
		# 關閉 NVDA 時，儲存開關狀態到使用者設定檔。
		self.potPlayer.terminate()
		conf.write()
		gui.toolsMenu.DestroyItem(self.menu.menuItem.Id)
		
		sound.free()
	
	@staticmethod
	def isRunningOnSecureDesktop():
		return appArgs.secure
	
	def startReadSubtitle(self):
		self.readSubtitleTimer.Start(0, wx.TIMER_CONTINUOUS)
	
	def stopReadSubtitle(self):
		self.readSubtitleTimer.Stop()
	
	def script_toggleSwitch(self, gesture):
		switch = conf['switch'] = not conf['switch']
		if switch:
			self.executeSubtitleExtractor()
			# Translators: This will be displayed when the reader switch is turned on
			ui.message(_(u'開始閱讀字幕'))
		else:
			self.stopReadSubtitle()
			# Translators: This will be displayed when the reader switch is turned off
			ui.message(_(u'停止閱讀字幕'))
		
		self.menu.switch.Check(switch)
	
	# Translators: Reader's toggle switch
	script_toggleSwitch.__doc__ = _(u'閱讀器開關')
	
	def script_manualReadSubtitle(self, gesture):
		def getSubtitle(self):
			obj = self.focusObject
			if obj.appModule.appName not in self.supportedBrowserAppNames:
				return
			
			extractor = self.getSubtitleExtractor()
			if not extractor:
				return
			
			extractor = extractor(self)
			videoPlayer = self.videoPlayer = extractor.getVideoPlayer()
			if not videoPlayer:
				return
			
			container = self.subtitleContainer = extractor.getSubtitleContainer()
			if not container:
				return
			
			return extractor.getSubtitle()
		
		try:	
			subtitle = getSubtitle(self)
		except (COMError, RuntimeError):
			subtitle = None
		
		if not subtitle:
			return ui.message('沒有字幕')
		
		return ui.message(subtitle)
	script_manualReadSubtitle.__doc__ = '手動閱讀字幕'
	
	def findUrl(self):
		window = api.getForegroundObject()
		windowHandle = window.windowHandle
		if windowHandle in self.urlObjects:
			return self.urlObjects[windowHandle]
		
		browser = window.appModule.appName
		inspectionObjects = [window]
		timestamp = time.time()
		timeout = 0.5
		
		while inspectionObjects:
			if time.time() - timestamp >= timeout:
				return
			
			obj = inspectionObjects.pop(0)
			found = False
			try:
				if browser == 'firefox':
					found = obj.IA2Attributes.get('id') == 'urlbar-input'
				else:
					found = obj.keyboardShortcut == 'Ctrl+L'
				
				if found:
					self.urlObjects[windowHandle] = obj
					return obj
				
				nextObj = obj.next
				if nextObj:
					inspectionObjects.insert(0, nextObj)
				
				nextObj = obj.firstChild
				if nextObj:
					inspectionObjects.insert(0, nextObj)
				
			
			except COMError:
				pass
			
		
	
	def event_foreground(self, obj, nextHandler):
		nextHandler()
		if not conf['backgroundReading']:
			self.stopReadSubtitle()
			self.videoPlayer = None
		
		if obj.appModule.appName not in self.supportedBrowserAppNames:
			return
		
		self.urlObject = self.findUrl()
	
	def event_gainFocus(self, obj, call_to_skip_event):
		'''
		取得新焦點時，重新取得字幕演算法。
		'''
		call_to_skip_event()
		
		self.focusObject = obj
		try:
			self.executeSubtitleExtractor()
		except (COMError, RuntimeError):
			pass
		
	
	def executeSubtitleExtractor(self):
		obj = self.focusObject
		if obj.role == 0:
			# 嵌入的 Youtube 頁框，在開始播放約 5 秒之後，會將焦點拉到一個不明的物件上，且 NVDA 無法查看其相鄰的物件，故將他跳過。
			return
		
		if not conf['switch']:
			return
		
		if obj.appModule.appName not in self.supportedBrowserAppNames:
			return
		
		extractor = self.getSubtitleExtractor()
		if not extractor:
			return
		
		self.subtitleExtractor = extractor = extractor(self)
		
		videoPlayer = self.videoPlayer = extractor.getVideoPlayer()
		if not videoPlayer:
			return
		
		container = self.subtitleContainer = extractor.getSubtitleContainer()
		if not container:
			return
		
		self.startReadSubtitle()
	
	def getSubtitleExtractor(self):
		window = self.focusObject.objectInForeground().name
		url = getattr(self.urlObject, 'value', '')
		for extractor in SubtitleExtractor.extractors:
			if extractor.windowTitle and re.match(extractor.windowTitle, window):
				return extractor
			
			if extractor.url and re.match(extractor.url, url):
				return extractor
			
		
	
	def readSubtitle(self):
		'''
		尋找並閱讀字幕，必須不斷執行。
		'''
		if not conf['switch'] or not self.subtitleContainer:
			return
		
		if not self.videoPlayer or not self.videoPlayer.role:
			return
		
		elapsedTime = time.time() - self.startReadSubtitleTime
		if elapsedTime < 0.1:
			return
		
		self.startReadSubtitleTime = time.time()
		try:
			self.subtitleExtractor.onReadingSubtitle()
			subtitle = self.subtitleExtractor.getSubtitle()
		except (COMError, RuntimeError):
			subtitle = None
		
		if subtitle is None:
			return
		
		self.processSubtitle(subtitle)
	
	def processSubtitle(self, subtitle):
		# 刪除用於渲染字幕效果的符號
		subtitle = subtitle.replace(u'​', '').replace(u' ', ' ')
		log.debug('original subtitle = ' + subtitle)
		subtitle = self.filterSamePart(subtitle)
		
		if not subtitle:
			# 沒有字幕超過一秒鐘才清除字幕緩衝區。
			if not self.emptySubtitleTime:
				self.emptySubtitleTime = time.time()
			elif time.time() - self.emptySubtitleTime >= 1:
				self.subtitle = ''
			
			return
		
		self.emptySubtitleTime = 0
		
		if subtitle == self.subtitle:
			return
		
		lastSubtitle = self.subtitle
		lastSubtitleText = lastSubtitle.replace(' | ', ' ')
		subtitleText = subtitle.replace(' | ', ' ')
		self.subtitle = subtitle
		
		msg = subtitleText
		
		# 若新的字幕內容是前一字幕的一部分，則不報讀。
		if subtitleText in lastSubtitleText:
			msg = ''
		
		# 若新的字幕包含前一字幕的內容，則只報讀填充的部分。
		if lastSubtitleText and lastSubtitleText in subtitleText:
			msg = subtitleText.replace(lastSubtitleText, '', 1)
		
		# 使用分隔符號來忽略兩次字幕之間相同的內容
		split = subtitle.split(' | ')
		for part in split:
			part = part.replace(' | ', ' ')
			if part in lastSubtitleText:
				msg = msg.replace(part, '')
			
		
		log.debug('subtitle = ' + subtitle)
		log.debug('last subtitle = ' + lastSubtitle)
		log.debug('msg = ' + msg)
		
		if not msg:
			msg = None
		
		ui.message(msg)
	
	def filterSamePart(self, subtitle):
		parts = subtitle.split(' | ')
		newParts = []
		for part in parts:
			if any(s for s in newParts if part.strip() in s.strip() or part.strip() == s.strip()):
				continue
			
			matchPart = [s for s in newParts if s.strip() in part.strip()]
			if matchPart:
				newParts.remove(matchPart[0])
			
			newParts.append(part)
		
		return ' | '.join(newParts)
	
	def toggleBackgroundReading(self, evt):
		conf['backgroundReading'] = not conf['backgroundReading']
		self.menu.backgroundReading.Check(conf['backgroundReading'])
	
	def toggleReadChat(self, evt):
		conf['readChat'] = not conf['readChat']
		self.menu.readChat.Check(conf['readChat'])
	
	def toggleReadChatSender(self, evt):
		conf['readChatSender'] = not conf['readChatSender']
		self.menu.readChatSender.Check(conf['readChatSender'])
	
	def toggleOnlyReadManagersChat(self, evt):
		conf['onlyReadManagersChat'] = not conf['onlyReadManagersChat']
		self.menu.onlyReadManagersChat.Check(conf['onlyReadManagersChat'])
	
	def toggleReadChatGiftSponser(self, evt):
		conf['readChatGiftSponser'] = not conf['readChatGiftSponser']
		self.menu.readChatGiftSponser.Check(conf['readChatGiftSponser'])
	
	def toggleOmitChatGraphic(self, evt):
		conf['omitChatGraphic'] = not conf['omitChatGraphic']
		self.menu.omitChatGraphic.Check(conf['omitChatGraphic'])
	
	def toggleInfoCardPrompt(self, evt):
		conf['infoCardPrompt'] = not conf['infoCardPrompt']
		self.menu.infoCardPrompt.Check(conf['infoCardPrompt'])
	
	# 聯絡開發者
	def contactUseWhatsApp(self, evt):
		webbrowser.open('https://wa.me/+886925285060')
	
	def contactUseLine(self, evt):
		api.copyToClip('Maxe0310', notify=True)
	
	def contactUseDiscord(self, evt):
		api.copyToClip('maxe0310', notify=True)
	
	def contactUseFacebook(self, evt):
		webbrowser.open('https://www.facebook.com/profile.php?id=100002631752665')
	
	def contactUseQq(self, evt):
		webbrowser.open('tencent://AddContact/?fromId=45&fromSubId=1&subcmd=all&uin=2231691423')
	
	def contactUseX(self, evt):
		webbrowser.open('https://www.x.com/Maxe0310')
	
	def openPlatformPage(self, evt):
		url = evt.GetEventObject().GetHelpString(evt.GetId())
		webbrowser.open(url)

	def onCrunchyrollTMChrome(self, evt):
		from .subtitleExtractors.crunchyroll import Crunchyroll
		Crunchyroll.installTampermonkey('chrome')

	def onCrunchyrollTMFirefox(self, evt):
		from .subtitleExtractors.crunchyroll import Crunchyroll
		Crunchyroll.installTampermonkey('firefox')

	def onCrunchyrollTMEdge(self, evt):
		from .subtitleExtractors.crunchyroll import Crunchyroll
		Crunchyroll.installTampermonkey('msedge')

	def onCrunchyrollInstallScript(self, evt):
		from .subtitleExtractors.crunchyroll import Crunchyroll
		Crunchyroll.installUserscript()

	def onCrunchyrollHelp(self, evt):
		ui.browseableMessage(
			_(u'Crunchyroll 字幕支援安裝說明\n\n'
			u'步驟一：安裝 Tampermonkey\n'
			u'在選單中選擇您的瀏覽器（Chrome、Firefox 或 Edge），\n'
			u'從開啟的頁面安裝 Tampermonkey 擴充功能。\n\n'
			u'步驟二：安裝腳本\n'
			u'點選「安裝腳本」，瀏覽器會開啟安裝頁面，\n'
			u'Tampermonkey 會自動提示安裝。\n'
			u'點選「安裝」，完成後關閉該分頁。\n\n'
			u'步驟三：使用\n'
			u'開啟 Crunchyroll 影片並啟用字幕，\n'
			u'按 NVDA+Y 開始閱讀字幕。\n\n'
			u'注意：支援 Chrome、Firefox 和 Edge。'),
			_(u'Crunchyroll 使用說明')
		)

	__gestures = {
		'kb:nvda+y': 'toggleSwitch',
	}
