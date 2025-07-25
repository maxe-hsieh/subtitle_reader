"""
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
from .youtube import Youtube
from .marumaruX import MarumaruX
from .disney_plus import DisneyPlus
from .netflix import Netflix
from .appleTVPlus import AppleTVPlus
from .crunchyroll import Crunchyroll
from .wkMediaCommons import WKMediaCommons
from .kktv import Kktv
from .lineTV import LineTV
from .meWatch import MeWatch
from .bilibili import Bilibili
from .iqy import Iqy
from .adn import Adn
from .missevan import Missevan
from .primeVideo import PrimeVideo
from .potPlayer import PotPlayer
from .update import Update

nvdaGui = gui.gui
wx = gui.wx

conf.load(appArgs.configPath + r'\subtitle_reader.json')

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    # Translators: Script category for Subtitle Reader
    scriptCategory = _(u'字幕閱讀器')
    def __new__(cls):
        if cls.isRunningOnSecureDesktop():
            return globalPluginHandler.GlobalPlugin()
        
        return super(cls, cls).__new__(cls)
    
    def __init__(self, *args, **kwargs):
        super(GlobalPlugin, self).__init__(*args, **kwargs)
        self.subtitleAlgs = {
            '.+ - YouTube': Youtube(self),
            '.+ \| 唱歌學.+ \| marumaru': MarumaruX(self),
            '.+ \| Disney\+': DisneyPlus(self),
            '.*?Netflix': Netflix(self),
            '^Prime Video.+': PrimeVideo(self),
            '.+ Apple TV\+': AppleTVPlus(self),
            '.+ - Wikimedia Commons': WKMediaCommons(self),
            '.+ \| KKTV': Kktv(self),
            '.+LINE TV-': LineTV(self),
            '.+ - mewatch': MeWatch(self),
            '.+_哔哩哔哩_bilibili': Bilibili(self),
            '.+愛奇藝 iQIYI': Iqy(self),
            '.+ \| ADN': Adn(self),
        }
        self.urlToSubtitleAlg = {
            '.*missevan.com/sound/player\?id=.+': Missevan(self),
            '.*animedigitalnetwork.fr/video/.*': Adn(self),
        }
        self.subtitleAlg = None
        self.supportedBrowserAppNames = ('chrome', 'brave', 'firefox', 'msedge')
        self.focusObject = None
        self.urlObjects = {}
        self.videoPlayer = None
        self.subtitleContainer = None
        self.subtitle = str()
        self.emptySubtitleTime = 0
        self.readSubtitleTimer = nvdaGui.NonReEntrantTimer(self.readSubtitle)
        self.startReadSubtitleTime = 0
        
        # --- NOUVEL AJOUT : Drapeau pour la gestion de la région live ---
        self.is_live_region_set = False
        
        sound.init()
        
        self.update = Update()
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
        menu.contactDeveloper.Bind(gui.wx.EVT_MENU, self.contactUseWhatsApp, menu.contactUseWhatsApp)
        menu.contactDeveloper.Bind(gui.wx.EVT_MENU, self.contactUseFacebook, menu.contactUseFacebook)
        menu.contactDeveloper.Bind(gui.wx.EVT_MENU, self.contactUseQq, menu.contactUseQq)
        menu.contactDeveloper.Bind(gui.wx.EVT_MENU, self.contactUseLine, menu.contactUseLine)
        menu.contactDeveloper.Bind(gui.wx.EVT_MENU, self.contactUseDiscord, menu.contactUseDiscord)
        menu.contactDeveloper.Bind(gui.wx.EVT_MENU, self.contactUseX, menu.contactUseX)
        
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
            self.executeSubtitleAlg()
            ui.message(_(u'開始閱讀字幕'))
        else:
            self.stopReadSubtitle()
            ui.message(_(u'停止閱讀字幕'))
        
        self.menu.switch.Check(switch)
    
    script_toggleSwitch.__doc__ = _(u'閱讀器開關')
    
    def script_manualReadSubtitle(self, gesture):
        def getSubtitle(self):
            obj = self.focusObject
            if obj.appModule.appName not in self.supportedBrowserAppNames:
                return
            
            alg = self.getSubtitleAlg()
            if not alg:
                return
            
            videoPlayer = self.videoPlayer = alg.getVideoPlayer()
            if not videoPlayer:
                return
            
            container = self.subtitleContainer = alg.getSubtitleContainer()
            if not container:
                return
            
            return alg.getSubtitle()
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
            # --- MODIFICATION : Réinitialise le drapeau si on quitte la fenêtre ---
            self.is_live_region_set = False
        
        if obj.appModule.appName not in self.supportedBrowserAppNames:
            return
        
        self.urlObject = self.findUrl()
    
    def event_gainFocus(self, obj, call_to_skip_event):
        call_to_skip_event()
        
        self.focusObject = obj
        try:
            self.executeSubtitleAlg()
        except (COMError, RuntimeError):
            pass
        
    
    def executeSubtitleAlg(self):
        obj = self.focusObject
        if obj.role == 0:
            return
        
        if not conf['switch']:
            return
        
        if obj.appModule.appName not in self.supportedBrowserAppNames:
            return
        
        alg = self.getSubtitleAlg()
        if not alg:
            # --- MODIFICATION : Réinitialise le drapeau si on n'est plus sur un site supporté ---
            self.is_live_region_set = False
            return
        
        self.subtitleAlg = alg
        
        videoPlayer = self.videoPlayer = alg.getVideoPlayer()
        if not videoPlayer:
            return
        
        container = self.subtitleContainer = alg.getSubtitleContainer()
        if not container:
            return
        
        # --- NOUVELLE LOGIQUE : Appel pour rendre la zone de sous-titres "live" ---
        # On vérifie que le drapeau n'est pas déjà activé
        if not self.is_live_region_set:
            # On vérifie que la méthode existe bien dans le handler du site actuel (ex: Adn)
            # pour éviter les erreurs sur les autres sites comme YouTube.
            if hasattr(alg, 'makeSubtitleContainerLive'):
                success = alg.makeSubtitleContainerLive()
                # Si l'opération réussit, on active le drapeau.
                if success:
                    self.is_live_region_set = True
        
        self.startReadSubtitle()
    
    def getSubtitleAlg(self):
        window = self.focusObject.objectInForeground().name
        url = getattr(self.urlObject, 'value', '')
        for alg in self.subtitleAlgs:
            if re.match(alg, window):
                return self.subtitleAlgs[alg]
            
        
        for alg in self.urlToSubtitleAlg:
            if re.match(alg, url):
                return self.urlToSubtitleAlg[alg]
            
        
    
    def readSubtitle(self):
        if not conf['switch'] or not self.subtitleContainer:
            return
        
        if not self.videoPlayer or not self.videoPlayer.role:
            return
        
        elapsedTime = time.time() - self.startReadSubtitleTime
        if elapsedTime < 0.1:
            return
        
        self.startReadSubtitleTime = time.time()
        try:
            self.subtitleAlg.onReadingSubtitle()
            subtitle = self.subtitleAlg.getSubtitle()
        except (COMError, RuntimeError):
            subtitle = None
        
        if subtitle is None:
            return
        
        self.processSubtitle(subtitle)
    
    def processSubtitle(self, subtitle):
        subtitle = subtitle.replace(u'​', '').replace(u' ', '')
        log.debug('original subtitle = ' + subtitle)
        subtitle = self.filterSamePart(subtitle)
        
        if not subtitle:
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
        
        if subtitleText in lastSubtitleText:
            msg = ''
        
        if lastSubtitleText and lastSubtitleText in subtitleText:
            msg = subtitleText.replace(lastSubtitleText, '', 1)
        
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
    
    __gestures = {
        'kb:nvda+y': 'toggleSwitch',
    }
"""


"""
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
from .youtube import Youtube
from .marumaruX import MarumaruX
from .disney_plus import DisneyPlus
from .netflix import Netflix
from .appleTVPlus import AppleTVPlus
from .wkMediaCommons import WKMediaCommons
from .kktv import Kktv
from .lineTV import LineTV
from .meWatch import MeWatch
from .bilibili import Bilibili
from .iqy import Iqy
from .adn import Adn
from .missevan import Missevan
from .primeVideo import PrimeVideo
from .potPlayer import PotPlayer
from .update import Update

nvdaGui = gui.gui
wx = gui.wx

conf.load(appArgs.configPath + r'\subtitle_reader.json')

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	# Translators: Script category for Subtitle Reader
	scriptCategory = _(u'字幕閱讀器')
	def __new__(cls):
		if cls.isRunningOnSecureDesktop():
			return globalPluginHandler.GlobalPlugin()
		
		return super(cls, cls).__new__(cls)
	
	def __init__(self, *args, **kwargs):
		super(GlobalPlugin, self).__init__(*args, **kwargs)
		self.subtitleAlgs = {
			'.+ - YouTube': Youtube(self),
			'.+ \| 唱歌學.+ \| marumaru': MarumaruX(self),
			'.+ \| Disney\+': DisneyPlus(self),
			'.*?Netflix': Netflix(self),
			'.+ - Watch on Crunchyroll': Crunchyroll(self),
			'^Prime Video.+': PrimeVideo(self),
			'.+ Apple TV\+': AppleTVPlus(self),
			'.+ - Wikimedia Commons': WKMediaCommons(self),
			'.+ \| KKTV': Kktv(self),
			'.+LINE TV-': LineTV(self),
			'.+ - mewatch': MeWatch(self),
			'.+_哔哩哔哩_bilibili': Bilibili(self),
			'.+愛奇藝 iQIYI': Iqy(self),
			'.+ \| ADN': Adn(self),
		}
		self.urlToSubtitleAlg = {
			'.*missevan.com/sound/player\?id=.+': Missevan(self),
			'.*animedigitalnetwork.fr/video/.*': Adn(self),
		}
		self.subtitleAlg = None
		self.supportedBrowserAppNames = ('chrome', 'brave', 'firefox', 'msedge')
		self.focusObject = None
		self.urlObjects = {}
		self.videoPlayer = None
		self.subtitleContainer = None
		self.subtitle = str()
		self.emptySubtitleTime = 0
		self.readSubtitleTimer = nvdaGui.NonReEntrantTimer(self.readSubtitle)
		self.startReadSubtitleTime = 0
		
		sound.init()
		
		self.update = Update()
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
		menu.contactDeveloper.Bind(gui.wx.EVT_MENU, self.contactUseWhatsApp, menu.contactUseWhatsApp)
		menu.contactDeveloper.Bind(gui.wx.EVT_MENU, self.contactUseFacebook, menu.contactUseFacebook)
		menu.contactDeveloper.Bind(gui.wx.EVT_MENU, self.contactUseQq, menu.contactUseQq)
		menu.contactDeveloper.Bind(gui.wx.EVT_MENU, self.contactUseLine, menu.contactUseLine)
		menu.contactDeveloper.Bind(gui.wx.EVT_MENU, self.contactUseDiscord, menu.contactUseDiscord)
		menu.contactDeveloper.Bind(gui.wx.EVT_MENU, self.contactUseX, menu.contactUseX)
		
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
			self.executeSubtitleAlg()
			ui.message(_(u'開始閱讀字幕'))
		else:
			self.stopReadSubtitle()
			ui.message(_(u'停止閱讀字幕'))
		
		self.menu.switch.Check(switch)
	
	script_toggleSwitch.__doc__ = _(u'閱讀器開關')
	
	def script_manualReadSubtitle(self, gesture):
		def getSubtitle(self):
			obj = self.focusObject
			if obj.appModule.appName not in self.supportedBrowserAppNames:
				return
			
			alg = self.getSubtitleAlg()
			if not alg:
				return
			
			videoPlayer = self.videoPlayer = alg.getVideoPlayer()
			if not videoPlayer:
				return
			
			container = self.subtitleContainer = alg.getSubtitleContainer()
			if not container:
				return
			
			return alg.getSubtitle()
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
		call_to_skip_event()
		
		self.focusObject = obj
		try:
			self.executeSubtitleAlg()
		except (COMError, RuntimeError):
			pass
		
	
	def executeSubtitleAlg(self):
		obj = self.focusObject
		if obj.role == 0:
			return
		
		if not conf['switch']:
			return
		
		if obj.appModule.appName not in self.supportedBrowserAppNames:
			return
		
		alg = self.getSubtitleAlg()
		if not alg:
			return
		
		self.subtitleAlg = alg
		
		videoPlayer = self.videoPlayer = alg.getVideoPlayer()
		if not videoPlayer:
			return
		
		container = self.subtitleContainer = alg.getSubtitleContainer()
		if not container:
			return
		
		self.startReadSubtitle()
	
	def getSubtitleAlg(self):
		window = self.focusObject.objectInForeground().name
		url = getattr(self.urlObject, 'value', '')
		for alg in self.subtitleAlgs:
			if re.match(alg, window):
				return self.subtitleAlgs[alg]
			
		
		for alg in self.urlToSubtitleAlg:
			if re.match(alg, url):
				return self.urlToSubtitleAlg[alg]
			
		
	
	def readSubtitle(self):
		if not conf['switch'] or not self.subtitleContainer:
			return
		
		if not self.videoPlayer or not self.videoPlayer.role:
			return
		
		elapsedTime = time.time() - self.startReadSubtitleTime
		if elapsedTime < 0.1:
			return
		
		self.startReadSubtitleTime = time.time()
		try:
			self.subtitleAlg.onReadingSubtitle()
			subtitle = self.subtitleAlg.getSubtitle()
		except (COMError, RuntimeError):
			subtitle = None
		
		if subtitle is None:
			return
		
		self.processSubtitle(subtitle)
	
	def processSubtitle(self, subtitle):
		subtitle = subtitle.replace(u'​', '').replace(u' ', '')
		log.debug('original subtitle = ' + subtitle)
		subtitle = self.filterSamePart(subtitle)
		
		if not subtitle:
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
		
		if subtitleText in lastSubtitleText:
			msg = ''
		
		if lastSubtitleText and lastSubtitleText in subtitleText:
			msg = subtitleText.replace(lastSubtitleText, '', 1)
		
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
		
		# --- MODIFICATION FINALE POUR FORCER LE FOCUS ---
		# On annonce le message uniquement s'il y a du contenu
		if msg:
			ui.message(msg)

		# Si un sous-titre a été lu, on tente de redonner le focus
		# au conteneur pour éviter qu'il ne "saute".
		if msg and self.subtitleContainer:
			try:
				self.subtitleContainer.setFocus()
			except (COMError, RuntimeError):
				# On ignore les erreurs si le focus ne peut pas être défini à ce moment précis.
				pass
	
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
	
	__gestures = {
		'kb:nvda+y': 'toggleSwitch',
	}
"""



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
from .youtube import Youtube
from .marumaruX import MarumaruX
from .disney_plus import DisneyPlus
from .netflix import Netflix
from .appleTVPlus import AppleTVPlus
from .wkMediaCommons import WKMediaCommons
from .kktv import Kktv
from .lineTV import LineTV
from .meWatch import MeWatch
from .bilibili import Bilibili
from .iqy import Iqy
from .adn import Adn
from .missevan import Missevan
from .primeVideo import PrimeVideo
from .potPlayer import PotPlayer
from .update import Update

nvdaGui = gui.gui
wx = gui.wx

conf.load(appArgs.configPath + r'\subtitle_reader.json')

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	# Translators: Script category for Subtitle Reader
	scriptCategory = _(u'字幕閱讀器')
	def __new__(cls):
		if cls.isRunningOnSecureDesktop():
			return globalPluginHandler.GlobalPlugin()
		
		return super(cls, cls).__new__(cls)
	
	def __init__(self, *args, **kwargs):
		super(GlobalPlugin, self).__init__(*args, **kwargs)
		self.subtitleAlgs = {
			'.+ - YouTube': Youtube(self),
			'.+ \| 唱歌學.+ \| marumaru': MarumaruX(self),
			'.+ \| Disney\+': DisneyPlus(self),
			'.*?Netflix': Netflix(self),
			'^Prime Video.+': PrimeVideo(self),
			'.+ Apple TV\+': AppleTVPlus(self),
			'.+ - Wikimedia Commons': WKMediaCommons(self),
			'.+ \| KKTV': Kktv(self),
			'.+LINE TV-': LineTV(self),
			'.+ - mewatch': MeWatch(self),
			'.+_哔哩哔哩_bilibili': Bilibili(self),
			'.+愛奇藝 iQIYI': Iqy(self),
			'.+ \| ADN': Adn(self),
		}
		self.urlToSubtitleAlg = {
			'.*missevan.com/sound/player\?id=.+': Missevan(self),
			'.*animedigitalnetwork.fr/video/.*': Adn(self),
		}
		self.subtitleAlg = None
		self.supportedBrowserAppNames = ('chrome', 'brave', 'firefox', 'msedge')
		self.focusObject = None
		self.urlObjects = {}
		self.videoPlayer = None
		self.subtitleContainer = None
		self.subtitle = str()
		self.emptySubtitleTime = 0
		self.readSubtitleTimer = nvdaGui.NonReEntrantTimer(self.readSubtitle)
		self.startReadSubtitleTime = 0
		
		sound.init()
		
		self.update = Update()
		self.initMenu()
		self.potPlayer = PotPlayer()
	
	def initMenu(self):
		menu = self.menu = gui.Menu(self)
		gui.tray.Bind(gui.wx.EVT_MENU, self.script_toggleSwitch, menu.switch)
		gui.tray.Bind(gui.wx.EVT_MENU, self.toggleBackgroundReading, menu.backgroundReading)
		# ... (le reste de initMenu reste identique)
	
	def terminate(self):
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
			self.executeSubtitleAlg()
			ui.message(_(u'開始閱讀字幕'))
		else:
			self.stopReadSubtitle()
			ui.message(_(u'停止閱讀字幕'))
		self.menu.switch.Check(switch)
	
	script_toggleSwitch.__doc__ = _(u'閱讀器開關')
	
	def script_manualReadSubtitle(self, gesture):
		def getSubtitle(self):
			obj = self.focusObject
			if obj.appModule.appName not in self.supportedBrowserAppNames: return
			alg = self.getSubtitleAlg()
			if not alg: return
			videoPlayer = self.videoPlayer = alg.getVideoPlayer()
			if not videoPlayer: return
			container = self.subtitleContainer = alg.getSubtitleContainer()
			if not container: return
			return alg.getSubtitle()
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
			if time.time() - timestamp >= timeout: return
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
				if nextObj: inspectionObjects.insert(0, nextObj)
				nextObj = obj.firstChild
				if nextObj: inspectionObjects.insert(0, nextObj)
			except COMError: pass
	
	def event_foreground(self, obj, nextHandler):
		nextHandler()
		if not conf['backgroundReading']:
			self.stopReadSubtitle()
			self.videoPlayer = None
		if obj.appModule.appName not in self.supportedBrowserAppNames:
			return
		self.urlObject = self.findUrl()
	
	def event_gainFocus(self, obj, call_to_skip_event):
		call_to_skip_event()
		self.focusObject = obj
		try:
			self.executeSubtitleAlg()
		except (COMError, RuntimeError):
			pass
	
	def executeSubtitleAlg(self):
		obj = self.focusObject
		if obj.role == 0: return
		if not conf['switch']: return
		if obj.appModule.appName not in self.supportedBrowserAppNames: return
		alg = self.getSubtitleAlg()
		if not alg: return
		self.subtitleAlg = alg
		videoPlayer = self.videoPlayer = alg.getVideoPlayer()
		if not videoPlayer: return
		container = self.subtitleContainer = alg.getSubtitleContainer()
		if not container: return
		self.startReadSubtitle()
	
	def getSubtitleAlg(self):
		window = self.focusObject.objectInForeground().name
		url = getattr(self.urlObject, 'value', '')
		for alg in self.subtitleAlgs:
			if re.match(alg, window): return self.subtitleAlgs[alg]
		for alg in self.urlToSubtitleAlg:
			if re.match(alg, url): return self.urlToSubtitleAlg[alg]
	
	def readSubtitle(self):
		if not conf['switch'] or not self.subtitleContainer: return
		if not self.videoPlayer or not self.videoPlayer.role: return
		elapsedTime = time.time() - self.startReadSubtitleTime
		if elapsedTime < 0.1: return
		self.startReadSubtitleTime = time.time()
		try:
			self.subtitleAlg.onReadingSubtitle()
			subtitle = self.subtitleAlg.getSubtitle()
		except (COMError, RuntimeError):
			subtitle = None
		if subtitle is None: return
		self.processSubtitle(subtitle)
	
	def processSubtitle(self, subtitle):
		# ... (la logique de traitement du texte du sous-titre reste identique)
		subtitle = subtitle.replace(u'​', '').replace(u' ', '')
		log.debug('original subtitle = ' + subtitle)
		subtitle = self.filterSamePart(subtitle)
		if not subtitle:
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
		if subtitleText in lastSubtitleText:
			msg = ''
		if lastSubtitleText and lastSubtitleText in subtitleText:
			msg = subtitleText.replace(lastSubtitleText, '', 1)
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

		# --- MODIFICATION FINALE (PLAN C) ---
		if msg:
			ui.message(msg)

		# On force le focus sur un objet plus stable pour éviter le "saut"
		if msg:
			try:
				# On vérifie que le handler du site (Adn) a bien la fonction _findMainPlayerContainer
				if hasattr(self.subtitleAlg, '_findMainPlayerContainer'):
					main_player_container = self.subtitleAlg._findMainPlayerContainer()
					if main_player_container:
						main_player_container.setFocus()
						# On ajoute un log pour voir si l'opération a réussi
						log.info("PLAN C: Focus forcé avec succès sur le conteneur principal.")
					else:
						log.warning("PLAN C: Conteneur principal du lecteur non trouvé pour forcer le focus.")
				else:
					# Plan de secours si la méthode n'existe pas : on utilise l'ancien conteneur
					if self.subtitleContainer:
						self.subtitleContainer.setFocus()
						log.info("PLAN C: Focus forcé (secours) sur le conteneur des sous-titres.")

			except (COMError, RuntimeError) as e:
				# CRUCIAL : On log l'erreur pour enfin savoir ce qui se passe si ça échoue.
				log.error(f"PLAN C - ERREUR en tentant de forcer le focus : {e}")
	
	def filterSamePart(self, subtitle):
		# ... (cette fonction reste identique)
		parts = subtitle.split(' | ')
		newParts = []
		for part in parts:
			if any(s for s in newParts if part.strip() in s.strip() or part.strip() == s.strip()): continue
			matchPart = [s for s in newParts if s.strip() in part.strip()]
			if matchPart: newParts.remove(matchPart[0])
			newParts.append(part)
		return ' | '.join(newParts)

	# ... (le reste du fichier avec les fonctions toggle... et contact... reste identique)
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
	
	__gestures = {
		'kb:nvda+y': 'toggleSwitch',
	}