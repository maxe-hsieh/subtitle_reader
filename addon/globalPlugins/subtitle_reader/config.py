#coding=utf-8

import codecs
import json

class Config(dict):
	def load(self, fileName):
		self.fileName = fileName
		# 讓預設值為 True
		self.update({
			'switch': True,
			'backgroundReading': True,
			'readChat': True,
			'readChatSender': False,
			'onlyReadManagersChat': False,
			'readChatGiftSponser': True,
			'omitChatGraphic': True,
			'infoCardPrompt': True,
			'readChapter': True,
			'checkUpdateAutomatic': True,
			'skipVersion': '0'
		})
		# 從使用者設定檔取得開關狀態
		try:
			with codecs.open(fileName) as file:
				self.update(json.load(file))
			
		except:
			pass
		
	
	def write(self):
		with codecs.open(self.fileName, 'w+', encoding='utf-8') as file:
			json.dump(self, file, ensure_ascii=False)
		
	

conf = Config()
