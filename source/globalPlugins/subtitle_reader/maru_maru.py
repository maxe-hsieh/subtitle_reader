#coding=utf-8

# 由於 Marumaru 是使用欠入 Youtube 頁框的方式，所以大部分與取得 Youtube 字幕的演算法相同。

from .youtube import Youtube as YoutubeAlg
from .compatible import role
from .object_finder import find

class MaruMaru(YoutubeAlg):
	def getSubtitleContainer(self):
		# 取得 Marumaru 網站上提供的中文字幕容器，位於嵌入的 Youtube 頁框下方
		subtitleContainer = None
		obj = self.main.videoPlayer
		obj = find(obj, 'parent', 'role', role('internalframe'))
		
		obj = find(obj, 'next', 'id', 'divLyrics')
		
		obj = obj.firstChild
		
		obj = find(obj, 'next', 'id', 'LyricsTranslate_zh')
		
		subtitleContainer = obj
		return subtitleContainer
	
	def getSubtitle(self):
		super(MaruMaru, self).getSubtitle()
		return super(YoutubeAlg, self).getSubtitle()
	
