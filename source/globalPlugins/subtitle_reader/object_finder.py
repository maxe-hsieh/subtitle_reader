from logHandler import log

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
		
		o = getattr(o, nextAttr)
	
	log.debug(attrName + ' = ' + str(attrValue) + ' not found. ')
