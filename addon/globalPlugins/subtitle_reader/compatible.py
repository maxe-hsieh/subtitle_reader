from versionInfo import version as nvdaVersion
import controlTypes

def role(name):
	name = name.upper()
	if nvdaVersion < '2021.2':
		return getattr(controlTypes, 'ROLE_' + name)
	else:
		return getattr(controlTypes.Role, name)
	
