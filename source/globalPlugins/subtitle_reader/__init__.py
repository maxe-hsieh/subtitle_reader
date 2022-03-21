#coding=utf-8

# 字幕閱讀器
# 作者：謝福恩 <maxe@mail.batol.net>
# 版本： 1.0

import re
import ui
import time

from globalPluginHandler import GlobalPlugin
from globalVars import appArgs
from nvwave import playWaveFile
from . import gui
from .config import conf
from .youtube import Youtube
from .maru_maru import MaruMaru
from .disney_plus import DisneyPlus
from .netflix import Netflix
from .update import Update

wx = gui.wx

conf.load(appArgs.configPath + r'\subtitle_reader.json')

class GlobalPlugin(GlobalPlugin):
	scriptCategory = u'字幕閱讀器'
	def __init__(self, *args, **kwargs):
		super(GlobalPlugin, self).__init__(*args, **kwargs)
		self.subtitleAlgs = {
			'.+ - YouTube': Youtube(self),
			'.+-MARUMARU': MaruMaru(self),
			'^Disney\+ \| ': DisneyPlus(self),
			'^Netflix': Netflix(self),
		}
		self.subtitleAlg = None
		self.supportedBrowserAppNames = ('chrome', 'brave', 'firefox', 'msedge')
		self.focusObject = None
		self.videoPlayer = None
		self.subtitleContainer = None
		self.subtitle = str()
		self.emptySubTitleTime = 0
		# 使用 wx.PyTimer 不斷執行函數
		self.read_subtitle_timer = wx.PyTimer(self.read_subtitle)
		
		self.update = Update()
		# 初始化選單
		self.initMenu()
	
	def initMenu(self):
		menu = self.menu = gui.Menu()
		gui.tray.Bind(gui.wx.EVT_MENU, self.script_toggleSwitch, menu.switch)
		gui.tray.Bind(gui.wx.EVT_MENU, self.toggleInfoCardPrompt, menu.infoCardPrompt)
		gui.tray.Bind(gui.wx.EVT_MENU, self.update.manualCheck, menu.checkForUpdate)
		gui.tray.Bind(gui.wx.EVT_MENU, self.update.toggleCheckAutomatic, menu.checkUpdateAutomatic)
		menu.switch.Check(conf['switch'])
		menu.infoCardPrompt.Check(conf['infoCardPrompt'])
		menu.checkUpdateAutomatic.Check(conf['checkUpdateAutomatic'])
	
	def terminate(self):
		# 關閉 NVDA 時，儲存開關狀態到使用者設定檔。
		conf.write()
	
	def stopReadSubtitle(self):
		self.read_subtitle_timer.Stop()
		self.videoPlayer = None
	
	def script_toggleSwitch(self, gesture):
		u'閱讀器開關'
		switch = conf['switch'] = not conf['switch']
		if switch:
			self.read_subtitle_timer.Start(100)
			ui.message(u'開始閱讀字幕')
		else:
			self.read_subtitle_timer.Stop()
			ui.message(u'停止閱讀字幕')
		
		self.menu.switch.Check(switch)
	
	def event_gainFocus(self, obj, call_to_skip_event):
		'''
		取得新焦點時，重新取得字幕演算法。
		'''
		call_to_skip_event()
		self.focusObject = obj
		self.executeSubtitleAlg()
	
	def executeSubtitleAlg(self):
		obj = self.focusObject
		if obj.role == 0:
			# 嵌入的 Youtube 頁框，在開始播放約 5 秒之後，會將焦點拉到一個不明的物件上，且 NVDA 無法查看其相鄰的物件，故將他跳過。
			return
		
		self.stopReadSubtitle()
		if not conf['switch']:
			return
		
		if obj.appModule.appName not in self.supportedBrowserAppNames:
			return
		
		alg = self.subtitleAlg = self.getSubtitleAlg()
		if not alg:
			return
		
		videoPlayer = self.videoPlayer = alg.getVideoPlayer()
		if not videoPlayer:
			return
		
		container = self.subtitleContainer = alg.getSubtitleContainer()
		if not container:
			return
		
		self.read_subtitle_timer.Start(100)
	
	def getSubtitleAlg(self):
		window = self.focusObject.objectInForeground().name
		for alg in self.subtitleAlgs:
			if re.match(alg, window):
				return self.subtitleAlgs[alg]
			
		
	
	def read_subtitle(self):
		'''
		尋找並閱讀字幕，必須不斷執行。
		'''
		if not conf['switch'] or not self.subtitleContainer:
			return
		
		subtitle = self.subtitleAlg.getSubtitle()
		# 刪除用於渲染字幕效果的符號
		subtitle = subtitle.replace(u'​', '')
		subtitle = subtitle.strip()
		if subtitle == self.subtitle:
			return
		if not subtitle:
			# 沒有字幕超過一秒鐘才清除字幕緩衝區。
			if not self.emptySubTitleTime:
				self.emptySubTitleTime = time.time()
			elif time.time() - self.emptySubTitleTime >= 1000:
				self.subtitle = ''
				self.emptySubTitleTime = 0
			
			return
		if subtitle:
			msg = subtitle
			# 若新的字幕開頭為前一字幕的內容，則只報讀填充的部分。
			n = subtitle.find(self.subtitle)
			if self.subtitle and n == 0:
				msg = subtitle.replace(self.subtitle, '', 1)
			
			ui.message(msg)
		
		self.subtitle = subtitle
	
	def toggleInfoCardPrompt(self, evt):
		conf['infoCardPrompt'] = not conf['infoCardPrompt']
		self.menu.infoCardPrompt.Check(conf['infoCardPrompt'])
	
	__gestures = {
		'kb:nvda+y': 'toggleSwitch',
	}
