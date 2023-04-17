import time

from logHandler import log

import core

def find(obj, nextAttr, attrName, attrValue):
	o = obj
	while o:
		value = getattr(o, attrName, None)
		if not value:
			try:
				value = o.IA2Attributes.get(attrName)
			except:
				pass
			
		
		if isinstance(attrValue, list) and value in attrValue:
			log.debug(attrName + ' = ' + str(value) + ' found in the list. ')
			return o
		
		if value == attrValue:
			log.debug(attrName + ' = ' + str(attrValue) + ' found. ')
			return o
		
		if attrName == 'class' and attrValue in value:
			log.debug(attrName + ' = ' + str(attrValue) + ' found. ')
			return o
		
		o = getattr(o, nextAttr)
	
	log.debug(attrName + ' = ' + str(attrValue) + ' not found. ')

def search(obj, condition, onFound, onNotFound=None, next=True, child=True, continueOnFound=False):
	searchObject = Search(obj, condition, onFound, onNotFound, next, child, continueOnFound)
	if not Search.isRunning:
		Search.isRunning = True
		searchObject.start()
	else:
		Search.objects.append(searchObject)
	
	return searchObject

class Search:
	objects = []
	isRunning = False
	startTime = 0
	def __init__(self, obj, condition, onFound, onNotFound=None, next=True, child=True, continueOnFound=False):
		self.next = next
		self.child = child
		self.condition = condition
		self.onFound = onFound
		self.onNotFound = onNotFound
		self.continueOnFound = continueOnFound
		self.inspectionObjects = []
		self.inspectionObjects.append(obj)
		self.cancelled = None
	
	def start(self):
		self.__search()
	
	def cancel(self):
		self.cancelled = True
		self.inspectionObjects.clear()
	
	@property
	def isStopped(self):
		return self.cancelled or not self.inspectionObjects
	
	def __search(self):
		startTime = self.__class__.startTime = time.time()
		while True:
			if self.cancelled:
				return self.nextSearch()
			
			elapsedTime = time.time() - startTime
			if elapsedTime >= 0.02:
				return core.callLater(0, self.__search)
			
			obj = self.inspectionObjects.pop(0)
			
			try:
				if self.condition(obj):
					self.onFound(obj)
					if not self.continueOnFound:
						self.inspectionObjects.clear()
						return self.nextSearch()
					
				
			
			except:
				pass
			
			try:
				if self.next:
					nextObj = obj.next
					if nextObj:
						self.inspectionObjects.insert(0, nextObj)
					
				
			
			except:
				pass
			
			try:
				if self.child:
					childObj = obj.firstChild
					if childObj:
						self.inspectionObjects.insert(0, childObj)
					
				
			
			except:
				pass
			
			if not self.inspectionObjects:
				if callable(self.onNotFound):
					self.onNotFound()
				
				return self.nextSearch()
			
		
	
	def nextSearch(self):
		if not self.__class__.objects:
			self.__class__.isRunning = False
			return
		
		self.__class__.objects.pop(0).start()
	
