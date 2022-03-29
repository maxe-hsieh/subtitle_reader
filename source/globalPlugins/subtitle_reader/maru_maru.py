#coding=utf-8

# 由於 Marumaru 是使用欠入 Youtube 頁框的方式，所以大部分與取得 Youtube 字幕的演算法相同。

from .youtube import Youtube as YoutubeAlg
from .compatible import role

class MaruMaru(YoutubeAlg):
	def getSubtitleContainer(self):
		# 取得 Marumaru 網站上提供的中文字幕容器，位於嵌入的 Youtube 頁框下方
		subtitleContainer = None
		obj = self.main.videoPlayer
		try:
			while obj.role != role('internalframe'):
				obj = obj.parent
			
			while obj.IA2Attributes.get('id') != 'divLyrics':
				obj = obj.next
			
			obj = obj.firstChild
			while obj:
				if obj.IA2Attributes.get('id') == 'LyricsTranslate_zh':
					subtitleContainer = obj
					return subtitleContainer
				
				obj = obj.next
			
		except:
			return
		
	
	def getSubtitle(self):
		super(MaruMaru, self).getSubtitle()
		return super(YoutubeAlg, self).getSubtitle()
	
