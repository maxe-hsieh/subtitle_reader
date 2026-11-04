#coding=utf-8

import addonHandler
addonHandler.initTranslation()

import os
import re
from sys import version_info
if version_info.major == 2:
	from urllib import quote_plus, urlopen
	from codecs import open
else:
	from urllib.request import urlopen
	from urllib.parse import quote_plus

import ssl
from threading import Thread
from time import time

from .sound import play, music, setVolume, getPos, replaceSounds

from .version import version
from .config import conf
from .gui import UpdateDialog, wx, gui as nvdaGui
from globalVars import appArgs
from logHandler import log
import ui

soundPath = os.path.dirname(__file__) + r'\assets\sounds'
cacertPath = os.path.dirname(__file__) + r'\assets\cacert.pem'
projectUrl = 'https://raw.githubusercontent.com/maxe-hsieh/subtitle_reader/main'
sourceUrl = 'https://raw.githubusercontent.com/maxe-hsieh/subtitle_reader/main/addon'
soundUrl = sourceUrl + '/globalPlugins/subtitle_reader/assets/sounds'
assetUrl = 'https://github.com/maxe-hsieh/subtitle_reader/releases/latest/download'
tempDir = os.getenv('temp')
# 連線卡住時不要讓執行緒永遠等待，單位是秒。
networkTimeout = 10
# 預先載入音效最多等待的秒數，超過就使用附加元件內的音效，避免更新視窗遲遲不出現。
preloadTimeout = 5
# 每次發現新版本都要重新下載並替換的音效。
# updateChecking、isLatestVersion 與 downloadError 一律使用附加元件內的檔案。
updateSounds = ('newVersionFound', 'updating', 'downloadCompleted', 'skipVersion', 'closeDialog')

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
	
	def openCurrentChangeLog(self, event):
		filePath = appArgs.configPath + r'\addons\subtitle_reader\doc\zh_TW\changelog.html'
		os.startfile(filePath)
	
	def openLatestChangeLog(self, event):
		filePath = 'https://github.com/maxe-hsieh/subtitle_reader/blob/main/addon/doc/zh_TW/changelog.md#%E6%9B%B4%E6%96%B0%E6%97%A5%E8%AA%8C'
		os.startfile(filePath)
	
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
		try:
			info = self.getNewVersion()
		except Exception as e:
			if not automatic:
				wx.CallAfter(self.checkError, e)
			
			return
		
		if not info:
			if not automatic:
				wx.CallAfter(self.isLatestVersion)
			
			return
		
		if automatic and info['version'] == conf['skipVersion']:
			return
		
		self.new = info
		sounds = self.downloadSounds(updateSounds)
		wx.CallAfter(self.onNewVersionFound, sounds)
	
	def onNewVersionFound(self, sounds):
		replaceSounds(sounds)
		play(soundPath + r'\newVersionFound.ogg')
		self.showDialog()
	
	def downloadSounds(self, names):
		# 同時下載，總等待時間才會接近最慢的一個檔案，而不是全部相加。
		sounds = {}
		threads = [Thread(target=self.downloadSound, args=(name, sounds), daemon=True) for name in names]
		for thread in threads:
			thread.start()
		
		deadline = time() + preloadTimeout
		for thread in threads:
			thread.join(max(deadline - time(), 0))
		
		# 回傳複本，逾時才完成的下載不會影響交給主執行緒的資料。
		return dict(sounds)
	
	def downloadSound(self, name, sounds):
		filename = name + '.ogg'
		try:
			ctx = ssl.create_default_context(cafile=cacertPath)
			with urlopen(soundUrl + '/' + filename, context=ctx, timeout=preloadTimeout) as res:
				sounds[soundPath + '\\' + filename] = res.read()
			
		except Exception as e:
			log.debug('Failed to download sound %s: %s' % (filename, e))
		
	
	def getNewVersion(self):
		info = {'version': 0, 'changelog': '', 'error': None}
		with urlopen(projectUrl + '/buildVars.py', timeout=networkTimeout) as res:
			text = res.read().decode('utf-8')
		
		newVersion = re.findall(r'addon_version ?= ?"(.+)",\r?', text)[0]
		if newVersion == version:
			return
		
		info['version'] = newVersion
		
		with urlopen(sourceUrl + '/doc/zh_TW/changelog.md', timeout=networkTimeout) as res:
			text = res.read().decode('utf-8')
		
		info['changelog'] = text
		return info
	
	def isLatestVersion(self):
		play(soundPath + r'\isLatestVersion.ogg')
		# Translators: This is a prompt to confirm that the reader is the latest version
		wx.MessageBox(_(u'您已升級到最新版本，祝您觀影愉快！'), _(u'恭喜'), style=wx.ICON_EXCLAMATION)
	
	def checkError(self, error):
		play(soundPath + r'\downloadError.ogg')
		# Translators: This is the prompt when checking for updates fails
		wx.MessageBox(_(u'檢查更新失敗') + u': ' + str(error), _(u'錯誤'), style=wx.ICON_ERROR)
	
	def showDialog(self):
		dlg = self.dialog = UpdateDialog(self.new['version'])
		dlg.isVisited = False
		dlg.changelogText.SetValue(self.new['changelog'])
		dlg.volumeSlider.Bind(wx.EVT_SCROLL, self.onVolumeChange)
		dlg.updateNow.Bind(wx.EVT_BUTTON, self.updateNow)
		dlg.skipVersion.Bind(wx.EVT_BUTTON, self.skipVersion)
		dlg.later.Bind(wx.EVT_BUTTON, self.later)
		dlg.Bind(wx.EVT_CHAR_HOOK, self.onKeyDown)
		dlg.Bind(wx.EVT_CLOSE, self.onClose)
		#nvdaGui.runScriptModalDialog(dlg)
		dlg.ShowWithoutActivating()
	
	def onVolumeChange(self, evt):
		volume = max(evt.Position, 10)
		evt.EventObject.SetValue(volume)
		evt.Skip()
		if not self.bgm:
			return
		
		setVolume(self.bgm, volume)
	
	def updateNow(self, event):
		if self.downloadThreadObj and self.downloadThreadObj.is_alive():
			return
		
		play(soundPath + r'\updating.ogg')
		self.dialog.changelogText.SetFocus()
		self.downloadThreadObj = Thread(target=self.downloadThread)
		self.downloadThreadObj.start()
	
	def downloadThread(self):
		filename = 'subtitle_reader.nvda-addon'
		try:
			file = self.downloadFile(assetUrl + '/' + filename, tempDir + '\\' + filename, reportHook=self.updateProgress)
			wx.CallAfter(self.finishDownload, file[0])
		except Exception as e:
			wx.CallAfter(self.downloadError, e)
		
	
	def finishDownload(self, filePath):
		play(soundPath + r'\downloadCompleted.ogg')
		if self.dialog:
			self.dialog.Close()
		
		try:
			os.startfile(filePath)
		except Exception as e:
			self.downloadError(e)
		
	
	def downloadFile(self, url, filePath, reportHook=None):
		# 下載 release 再學校或辦公室出現憑證無效的問題，所以我們自備憑證。
		ctx = ssl.create_default_context(cafile=cacertPath)
		with urlopen(url, context=ctx, timeout=networkTimeout) as response:
			total = int(response.headers.get('Content-Length', 0))
			current = 0
			with open(filePath, 'wb') as f:
				while True:
					data = response.read(8192)
					if not data:
						break
					
					f.write(data)
					current += len(data)
					if reportHook:
						reportHook(current, total)
					
				
			
		
		if current < total:
			raise Exception('Download failed, Size mismatch. ')
		
		return filePath, response.headers
	
	def updateProgress(self, current, total):
		percent = int(100 * current / total)
		wx.CallAfter(self.dialog.progress.SetValue, percent)
	
	def downloadError(self, error):
		play(soundPath + r'\downloadError.ogg')
		# Translators: This is the prompt when downloading updates fails
		wx.MessageBox(_(u'下載更新失敗') + u': ' + str(error), _(u'錯誤'), style=wx.ICON_ERROR, parent=self.dialog)
	
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
			setVolume(self.bgm, self.dialog.volumeSlider.Value)
			res = urlopen('https://raw.githubusercontent.com/maxe-hsieh/bgm/main/subtitle_reader/updating.ly', timeout=networkTimeout)
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
	
