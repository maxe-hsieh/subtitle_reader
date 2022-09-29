from .pybass import *

musicFile = None
musicFilename = ''
sound = None

def init():
	return BASS_Init(-1, -1, 0, 0, 0)

def play(filename=None):
	global sound
	if sound:
		BASS_StreamFree(sound)
		sound = None
	
	if not filename:
		return
	
	if filename.find('http') == 0:
		sound = BASS_StreamCreateURL(filename.encode('utf-8'), 0, BASS_STREAM_AUTOFREE, None, None)
	else:
		sound = BASS_StreamCreateFile(False, filename.encode('utf-8'), 0, 0, BASS_STREAM_AUTOFREE)
	
	BASS_ChannelPlay(sound, True)

def music(filename=None):
	global musicFile
	global musicFilename
	if filename and filename == musicFilename:
		return
	
	musicFilename = filename
	if musicFile:
		BASS_StreamFree(musicFile)
		musicFile = None
	
	if not filename:
		return
	
	if filename.find('http') == 0:
		musicFile = BASS_StreamCreateURL(filename.encode('utf-8'), 0, BASS_SAMPLE_LOOP, None, None)
	else:
		musicFile = BASS_StreamCreateFile(False, filename.encode('utf-8'), 0, 0, BASS_SAMPLE_LOOP)
	
	BASS_ChannelPlay(musicFile, True)
	return musicFile

def getPos(file):
	return BASS_ChannelBytes2Seconds(file, BASS_ChannelGetPosition(file, BASS_POS_BYTE))

def free():
	BASS_Free()
