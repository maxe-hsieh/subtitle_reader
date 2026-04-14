#coding=utf-8

import os
import webbrowser
import tempfile
import shutil

import api
import ui

from . import SubtitleExtractor, SupportStatus
from ..object_finder import find
from ..compatible import role

from logHandler import log

# URLs d'installation de Tampermonkey par navigateur
TAMPERMONKEY_URLS = {
	'chrome': 'https://chromewebstore.google.com/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo',
	'firefox': 'https://addons.mozilla.org/firefox/addon/tampermonkey/',
	'msedge': 'https://microsoftedge.microsoft.com/addons/detail/tampermonkey/iikmkjmpaadaobahmlepeloendndfphd',
}

class Crunchyroll(SubtitleExtractor):
	info = {
		'name': 'Crunchyroll',
		'url': 'https://www.crunchyroll.com/',
		'status': SupportStatus.supported,
	}
	windowTitle = '.+ (-|–) .+ Crunchyroll'
	@staticmethod
	def getUserscriptPath():
		return os.path.join(os.path.dirname(__file__), 'crunchyroll_subtitles.user.js')

	@staticmethod
	def installTampermonkey(browser=None):
		"""Ouvre la page d'installation de Tampermonkey pour le navigateur donne."""
		if browser and browser in TAMPERMONKEY_URLS:
			webbrowser.open(TAMPERMONKEY_URLS[browser])
			return True
		# Si pas de navigateur specifie, ouvrir pour tous
		for url in TAMPERMONKEY_URLS.values():
			webbrowser.open(url)
			return True
		return False

	@staticmethod
	def installUserscript():
		"""Cree une page HTML temporaire qui redirige vers le userscript pour installation automatique via Tampermonkey."""
		srcPath = Crunchyroll.getUserscriptPath()
		if not os.path.exists(srcPath):
			return False
		try:
			tmpDir = os.path.join(tempfile.gettempdir(), 'subtitle_reader')
			if not os.path.exists(tmpDir):
				os.makedirs(tmpDir)

			# Copier le userscript
			tmpScript = os.path.join(tmpDir, 'crunchyroll_subtitles.user.js')
			shutil.copy2(srcPath, tmpScript)
			scriptFileUrl = 'file:///' + tmpScript.replace('\\', '/')

			# Creer une page HTML qui redirige vers le script
			# Tampermonkey detecte les .user.js ouverts dans le navigateur
			htmlPath = os.path.join(tmpDir, 'install.html')
			with open(htmlPath, 'w', encoding='utf-8') as f:
				f.write('<!DOCTYPE html>\n<html><head>\n')
				f.write('<meta charset="utf-8">\n')
				f.write('<title>Installation du script Crunchyroll pour NVDA</title>\n')
				f.write('<meta http-equiv="refresh" content="2;url=' + scriptFileUrl + '">\n')
				f.write('</head><body>\n')
				f.write('<h1>Installation du script Crunchyroll Subtitle Reader</h1>\n')
				f.write('<p>Si Tampermonkey est installe, une fenetre d\'installation devrait apparaitre automatiquement.</p>\n')
				f.write('<p>Si rien ne se passe, <a href="' + scriptFileUrl + '">cliquez ici</a>.</p>\n')
				f.write('</body></html>')

			webbrowser.open('file:///' + htmlPath.replace('\\', '/'))
			return True
		except Exception:
			return False

	def getVideoPlayer(self):
		obj = self.main.focusObject
		videoPlayer = find(obj, 'parent', 'id', 'player-container')
		return videoPlayer

	def getSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		if not videoPlayer:
			return None

		# Chercher le bridge dans player-accessibility-announcer
		announcer = find(videoPlayer.firstChild, 'next', 'id', 'player-accessibility-announcer')
		if announcer:
			bridge = find(announcer.firstChild, 'next', 'id', 'nvda-subtitle-bridge')
			if bridge:
				return bridge

		# Fallback: chercher dans les enfants du player
		bridge = find(videoPlayer.firstChild, 'next', 'id', 'nvda-subtitle-bridge')
		if bridge:
			return bridge

		# Fallback: un niveau plus profond
		child = videoPlayer.firstChild
		while child:
			if child.firstChild:
				bridge = find(child.firstChild, 'next', 'id', 'nvda-subtitle-bridge')
				if bridge:
					return bridge
			child = child.next

		return None

	def getSubtitle(self):
		obj = self.main.subtitleContainer
		if not obj:
			return None
		text = obj.name
		if text:
			return text
		child = obj.firstChild
		if child and child.name:
			return child.name
		return None
