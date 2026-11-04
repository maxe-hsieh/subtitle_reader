from .pybass import *

musicFile = None
musicFilename = ''
sound = None
# 預先載入到記憶體的音效，以本機檔案路徑作為索引。
memorySounds = {}

def init():
	return BASS_Init(-1, -1, 0, 0, 0)

# 只能在主執行緒呼叫，背景執行緒請使用 wx.CallAfter。
def replaceSounds(sounds):
	# BASS 播放時會直接讀取這塊記憶體，所以必須先釋放串流，才能替換資料。
	play()
	memorySounds.update(sounds)

# 只能在主執行緒呼叫，背景執行緒請使用 wx.CallAfter。
# 同時從多個執行緒呼叫會留下未釋放的舊串流，之後替換資料時它會讀到已被丟棄的記憶體。
def play(filename=None):
	global sound
	if sound:
		BASS_StreamFree(sound)
		sound = None
	
	if not filename:
		return
	
	data = memorySounds.get(filename)
	if data:
		sound = BASS_StreamCreateFile(True, data, 0, len(data), BASS_STREAM_AUTOFREE)
	
	# 沒有預先載入，或載入的資料無法解碼時，改用原本的來源。
	if not sound:
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

def setVolume(sound, volume):
	volume /= 100
	BASS_ChannelSetAttribute(sound, BASS_ATTRIB_VOL, volume)

def getPos(file):
	return BASS_ChannelBytes2Seconds(file, BASS_ChannelGetPosition(file, BASS_POS_BYTE))

def free():
	BASS_Free()
