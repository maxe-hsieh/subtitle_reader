#coding=utf-8


import speech
import difflib
import winInputHook
import vkCodes
import api

from .config import conf


class PotPlayer:
	def __init__(self):
		self.lastSpeechText = ''
		self.oldProcessText = speech.speech.processText
		speech.speech.processText = self.processText
		self.oldKeyDown = winInputHook.keyDownCallback
		winInputHook.keyDownCallback = self.keyDown
	
	def terminate(self):
		speech.speech.processText = self.oldProcessText
		winInputHook.keyDownCallback = self.oldKeyDown
	
	def processText(self, locale, text, symbolLevel):
		text = self.oldProcessText(locale, text, symbolLevel)
		if not conf['switch']:
			return text
		
		if 'potplayermini' not in api.getForegroundObject().appModule.appName:
			return text
		
		ret = text
		if text == self.lastSpeechText:
			return text
		
		if len(text) < 6:
			self.lastSpeechText = text
			return text
		
		sameString = findSameString(self.lastSpeechText, text)
		if len(sameString) > 6 and (sameString[0] == text[0] or sameString[-1] == text[-1]):
			ret = ret.replace(sameString, '')
		
		self.lastSpeechText = text
		return ret
	
	def keyDown(self, vkCode, scanCode, extended, injected):
		if vkCode not in (vkCodes.byName['leftcontrol'][0], vkCodes.byName['rightcontrol'][0]):
			self.lastSpeechText = ''
		
		return self.oldKeyDown(vkCode, scanCode, extended, injected)
	


def findSameString(str1, str2):
	# 使用difflib的SequenceMatcher来找到最长的匹配子序列
	matcher = difflib.SequenceMatcher(None, str1, str2)
	match = matcher.find_longest_match(0, len(str1), 0, len(str2))
	
	if match.size > 0:
		return str1[match.a:match.a + match.size]
	else:
		return ''
	
