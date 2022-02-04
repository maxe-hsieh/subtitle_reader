def find(obj, nextAttr, attrName, attrValue):
	o = obj
	while o:
		value = getattr(o, attrName, None)
		if not value:
			try:
				value = o.IA2Attributes[attrName]
			except:
				pass
			
		
		if value == attrValue:
			return o
		
		o = getattr(o, nextAttr)
	
