#coding=utf-8

import addonHandler
addonHandler.initTranslation()

import os
import re
from sys import version_info
if version_info.major == 2:
	from urllib import quote_plus, urlopen, urlretrieve as downloadFile
	from codecs import open
else:
	from urllib.request import urlopen, urlretrieve as downloadFile
	from urllib.parse import quote_plus

from threading import Thread

from .sound import play, music, getPos

from .version import version
from .config import conf
from .gui import UpdateDialog, wx, gui as nvdaGui
from globalVars import appArgs
import ui

soundPath = os.path.dirname(__file__) + r'\sounds'
sourceUrl = 'https://raw.githubusercontent.com/maxe-hsieh/subtitle_reader/main/addon'
assetUrl = 'https://github.com/maxe-hsieh/subtitle_reader/releases/latest/download'
tempDir = os.getenv('temp')

class Update:
	def __init__(self):
		self.new = {}
		self.checkThreadObj = None
		self.dialog = None
		self.downloadThreadObj = None
		self.bgmThread = None
		self.bgm = None
		self.lastPos = 0
		self.readLyricsTimer = None
		self.checkAutomatic()
	
	def checkAutomatic(self):
		if not conf['checkUpdateAutomatic']:
			return
		
		self.execute(automatic=True)
		self.automaticTimer = nvdaGui.NonReEntrantTimer(self.checkAutomatic)
		self.automaticTimer.StartOnce(1000*60*60*2)
	
	def manualCheck(self, event):
		conf['skipVersion'] = '0'
		play(soundPath + r'\updateChecking.ogg')
		self.execute()
	
	def openChangeLog(self, event):
		filePath = appArgs.configPath + r'\addons\subtitle_reader\doc\zh_TW\changelog.html'
		os.system('start ' + filePath)
	
	def toggleCheckAutomatic(self, event):
		menu = event.GetEventObject()
		# Translators: This is Menu item that can toggle automatic check for update on Subtitle Reader is start
		id = menu.FindItem(_(u'自動檢查更新(&A)'))
		item = menu.FindItemById(id)
		status = conf['checkUpdateAutomatic'] = not conf['checkUpdateAutomatic']
		item.Check(status)
	
	def execute(self, automatic=False):
		if self.checkThreadObj and self.checkThreadObj.is_alive():
			return
		
		if self.dialog:
			return
		
		self.checkThreadObj = Thread(target=self.checkThread, kwargs={'automatic': automatic})
		self.checkThreadObj.start()
	
	def checkThread(self, automatic=False):
		info = self.getNewVersion()
		if not info:
			if not automatic:
				wx.CallAfter(self.isLatestVersion)
			
			return
		
		if info['error']:
			if not automatic:
				wx.CallAfter(self.checkError)
			
			return
		
		if automatic and info['version'] == conf['skipVersion']:
			return
		
		self.new = info
		play(soundPath + r'\newVersionFound.ogg')
		wx.CallAfter(self.showDialog)
	
	def getNewVersion(self):
		info = {'version': 0, 'changelog': '', 'error': None}
		try:
			res = urlopen(sourceUrl + '/manifest.ini')
			text = res.read().decode('utf-8')
			res.close()
			
			if res.getcode() != 200:
				info['error'] = True
				return info
			
			newVersion = re.findall(r'version ?= ?(.+)\r?', text)[0]
			if newVersion == version:
				return
			
			info['version'] = newVersion
			
			res = urlopen(sourceUrl + '/doc/zh_TW/changelog.md')
			text = res.read().decode('utf-8')
			res.close()
			
			info['changelog'] = text
			return info
		except:
			info['error'] = True
			return info
		
	
	def isLatestVersion(self):
		play(soundPath + r'\isLatestVersion.ogg')
		# Translators: This is a prompt to confirm that the reader is the latest version
		wx.MessageBox(_(u'您已升級到最新版本，祝您觀影愉快！'), _(u'恭喜'), style=wx.ICON_EXCLAMATION)
	
	def checkError(self):
		play(soundPath + r'\downloadError.ogg')
		# Translators: This is the prompt when checking for updates fails
		wx.MessageBox(_(u'檢查更新失敗'), _(u'錯誤'), style=wx.ICON_ERROR)
	
	def showDialog(self):
		dlg = self.dialog = UpdateDialog(self.new['version'])
		dlg.isVisited = False
		dlg.changelogText.SetValue(self.new['changelog'])
		dlg.updateNow.Bind(wx.EVT_BUTTON, self.updateNow)
		dlg.skipVersion.Bind(wx.EVT_BUTTON, self.skipVersion)
		dlg.later.Bind(wx.EVT_BUTTON, self.later)
		dlg.Bind(wx.EVT_CHAR_HOOK, self.onKeyDown)
		dlg.Bind(wx.EVT_CLOSE, self.onClose)
		#nvdaGui.runScriptModalDialog(dlg)
		dlg.ShowWithoutActivating()
	
	def updateNow(self, event):
		if self.downloadThreadObj and self.downloadThreadObj.is_alive():
			return
		
		play(soundPath + r'\updating.ogg')
		self.dialog.changelogText.SetFocus()
		self.downloadThreadObj = Thread(target=self.downloadThread)
		self.downloadThreadObj.start()
	
	def downloadThread(self):
		filename = 'subtitle_reader.nvda-addon'
		with open(tempDir + '\\' + filename, 'w'):
			pass
		
		try:
			file = downloadFile(assetUrl + '/' + filename, tempDir + '\\' + filename, reporthook=self.updateProgress)
			play(soundPath + r'\downloadCompleted.ogg')
			self.dialog.Close()
			os.system('start ' + file[0])
		except:
			wx.CallAfter(self.downloadError())
		
	
	def updateProgress(self, blockCount, blockSize, total):
		percent = 100 * blockCount * blockSize / total
		wx.CallAfter(self.dialog.progress.SetValue, percent)
	
	def downloadError(self):
		play(soundPath + r'\downloadError.ogg')
		# Translators: This is the prompt when downloading updates fails
		wx.MessageBox(_(u'下載更新失敗'), _(u'錯誤'), style=wx.ICON_ERROR, parent=self.dialog)
	
	def skipVersion(self, event):
		play(soundPath + r'\skipVersion.ogg')
		conf['skipVersion'] = self.new['version']
		self.dialog.Close()
	
	def later(self, event):
		play(soundPath + r'\closeDialog.ogg')
		self.dialog.Close()
	
	def onKeyDown(self, event):
		event.Skip()
		if self.dialog.isVisited:
			return
		
		self.dialog.isVisited = True
		self.bgmThread = Thread(target=self.startBGM)
		self.bgmThread.start()
	
	def startBGM(self):
		self.bgm = music('https://raw.githubusercontent.com/maxe-hsieh/bgm/main/subtitle_reader/updating.mp3')
		# 有可能在音樂播放之前視窗已經關閉
		if not self.dialog:
			music()
			self.bgm = None
			return
		
		try:
			res = urlopen('https://raw.githubusercontent.com/maxe-hsieh/bgm/main/subtitle_reader/updating.ly')
			if res.code != 200:
				return
			
			lyrics = res.read().decode('utf-8')
			res.close()
		
		except:
			return
		
		lyricsObj = []
		for line in lyrics.split('\n'):
			obj = {}
			match = re.match(r'^\[(\d{1,2}):(\d{1,2}(?:\.\d+)?)\](.+)$', line)
			if not match:
				continue
			
			obj['time'] = int(match.group(1)) * 60 + float(match.group(2))
			obj['text'] = match.group(3)
			lyricsObj.append(obj)
		
		self.lyrics = lyricsObj
		self.readLyricsTimer = nvdaGui.NonReEntrantTimer(self.readLyrics)
		wx.CallAfter(self.readLyricsTimer.Start, 5, wx.TIMER_CONTINUOUS)
	
	def readLyrics(self):
		second = round(getPos(self.bgm), 3)
		lyrics = ''
		if self.lastPos < second:
			for obj in self.lyrics:
				if self.lastPos <= obj['time'] < second:
					lyrics += obj['text'] + '\r\n'
				
			
		
		self.lastPos = second
		if not lyrics:
			return
		
		self.dialog.subtitleLabel.SetLabel(lyrics)
		if conf['switch'] is False:
			return
		
		if not self.dialog.IsActive():
			return
		
		ui.message(lyrics)
		
	
	def onClose(self, event):
		if self.readLyricsTimer is not None:
			self.readLyricsTimer.Stop()
			self.readLyricsTimer = None
		
		self.dialog.Destroy()
		self.dialog = None
		music()
		self.bgm = None
	
