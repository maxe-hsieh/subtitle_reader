#encoding=utf-8

from __future__ import absolute_import
import wx
import gui

tray = gui.mainFrame.sysTrayIcon
toolsMenu = tray.toolsMenu

class Menu(wx.Menu):
	def __init__(self):
		super(Menu, self).__init__()
		toolsMenu.AppendSubMenu(self, u'字幕閱讀器 (&Y)')
		self.switch = self.AppendCheckItem(wx.ID_ANY, u'閱讀器開關 (&S)')
		self.switch.Check(True)
		
		self.infoCardPrompt = self.AppendCheckItem(wx.ID_ANY, u'資訊卡提示(&I)')
		self.infoCardPrompt.Check(True)
		
		self.checkForUpdate = self.Append(wx.ID_ANY, u'立即檢查更新(&C)')
		
		self.checkUpdateOnStartup = self.AppendCheckItem(wx.ID_ANY, u'啟動時檢查更新(&A)')
		self.checkUpdateOnStartup.Check(True)
	

class UpdateDialog(wx.Dialog):
	def __init__(self):
		super(UpdateDialog, self).__init__(gui.mainFrame, title='字幕閱讀器新版資訊')
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.changeLogLabel = wx.StaticText(self, label='更新日誌')
		self.changelogText = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(700, -1))
		self.progress = wx.Gauge(self, style=wx.GA_VERTICAL)
		self.updateNow = wx.Button(self, label='現在更新(&U)')
		self.skipVersion = wx.Button(self, label='跳過此版本(&S)')
		self.later = wx.Button(self, label='晚點再說(&L)')
		self.SetSizerAndFit(self.sizer)
	
