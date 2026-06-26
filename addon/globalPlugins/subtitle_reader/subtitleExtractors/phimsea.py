#coding=utf-8

from . import SubtitleExtractor, SupportStatus
from ..object_finder import find
from ..compatible import role

from logHandler import log


class Phimsea(SubtitleExtractor):
	info = {
		'name': 'PhimSea',
		'url': 'https://phimsea.com/',
		'status': SupportStatus.supported,
	}
	windowTitle = ''
	url = r'.*phimsea\.com/watch/.*'
	PLAYER_ANCESTOR_CLASSES = ('vjs-tech', 'video-js')
	PLAYER_ANCESTOR_TAGS = ('media-player',)
	PLAYER_MARKER_CLASSES = ('video-js', 'vjs-text-track-display')
	PLAYER_MARKER_TAGS = ('media-player', 'media-captions')
	VIDEOJS_SUBTITLE_CLASSES = ('vjs-text-track-display',)
	VIDSTACK_SUBTITLE_CLASSES = ('vds-captions', 'media-captions')
	VIDSTACK_SUBTITLE_TAGS = ('media-captions',)
	TIME_CONTROL_MARKERS = (
		'vjs-current-time',
		'vjs-duration',
		'vjs-remaining-time',
		'vjs-time-control',
		'vjs-time-tooltip',
		'vjs-progress-control',
	)

	def getVideoPlayer(self):
		log.debug('PhimSea extractor selected.')
		focusObject = self.main.focusObject
		videoPlayer = self.findPlayerFromAncestors(focusObject)
		if videoPlayer:
			log.debug('PhimSea video player found from focus ancestors.')
			return videoPlayer

		if not self.canScanPageDocument():
			log.debug('PhimSea page scan skipped because URL is not confirmed.')
			return

		document = self.findDocument(focusObject)
		if not document:
			log.debug('PhimSea page document not found.')
			return

		videoPlayer = self.findPlayerMarker(document)
		if videoPlayer:
			log.debug('PhimSea video player found from page document.')
		else:
			log.debug('PhimSea video player not found.')
		return videoPlayer

	def findPlayerFromAncestors(self, obj):
		return self.findAncestorMatching(
			obj,
			classes=self.PLAYER_ANCESTOR_CLASSES,
			tags=self.PLAYER_ANCESTOR_TAGS,
		)

	def canScanPageDocument(self):
		try:
			url = self.main.urlObject.value or ''
		except:
			url = ''
		return 'phimsea.com/watch/' in url

	def findDocument(self, obj):
		return find(obj, 'parent', 'role', role('document'))

	def findPlayerMarker(self, obj):
		return self.findDescendantMatching(
			obj,
			classes=self.PLAYER_MARKER_CLASSES,
			tags=self.PLAYER_MARKER_TAGS,
		)

	def getSubtitleContainer(self):
		videoPlayer = self.main.videoPlayer
		container = self.getVideojsSubtitleContainer(videoPlayer)
		container = container or self.getVidstackSubtitleContainer(videoPlayer)
		if container:
			log.debug('PhimSea subtitle container found.')
		else:
			log.debug('PhimSea subtitle container not found.')
		return container

	def getVideojsSubtitleContainer(self, obj):
		if self.hasAnyClass(obj, self.VIDEOJS_SUBTITLE_CLASSES):
			return obj

		container = self.findDescendantMatching(obj, classes=self.VIDEOJS_SUBTITLE_CLASSES)
		container = container or self.findNextByClass(obj, 'vjs-text-track-display')
		if not container:
			container = self.findDescendantMatching(
				getattr(obj, 'parent', None),
				classes=self.VIDEOJS_SUBTITLE_CLASSES,
			)
		return container

	def getVidstackSubtitleContainer(self, obj):
		return self.findDescendantMatching(
			obj,
			classes=self.VIDSTACK_SUBTITLE_CLASSES,
			tags=self.VIDSTACK_SUBTITLE_TAGS,
		)

	def findNextByClass(self, obj, className):
		try:
			return find(obj, 'next', 'class', className)
		except:
			return

	def findAncestorMatching(self, obj, classes=(), tags=()):
		current = obj
		visitedObjects = set()
		limit = 50
		while current and limit > 0:
			limit -= 1
			key = self.getObjectKey(current)
			if key in visitedObjects:
				return
			visitedObjects.add(key)

			if self.matchesObject(current, classes, tags):
				return current

			try:
				current = current.parent
			except:
				return

	def findDescendantMatching(self, obj, classes=(), tags=()):
		return self.findDescendant(obj, lambda obj: self.matchesObject(obj, classes, tags))

	def findDescendant(self, obj, condition):
		for current in self.walkSubtree(obj, 500):
			try:
				if condition(current):
					return current
			except:
				pass

	def walkSubtree(self, obj, limit):
		if not obj:
			return

		inspectionObjects = [(obj, True)]
		visitedObjects = set()
		while inspectionObjects and limit > 0:
			limit -= 1
			current, isRoot = inspectionObjects.pop()
			key = self.getObjectKey(current)
			if key in visitedObjects:
				continue
			visitedObjects.add(key)
			yield current

			try:
				if not isRoot:
					nextObject = current.next
					if nextObject:
						inspectionObjects.append((nextObject, False))
			except:
				pass

			try:
				child = current.firstChild
				if child:
					inspectionObjects.append((child, False))
			except:
				pass

	def matchesObject(self, obj, classes=(), tags=()):
		return self.hasAnyClass(obj, classes) or self.hasAnyTag(obj, tags)

	def hasAnyClass(self, obj, classes):
		value = self.getObjectAttribute(obj, 'class')
		return any(className in value for className in classes)

	def hasAnyTag(self, obj, tags):
		value = self.getObjectAttribute(obj, 'tag').lower()
		return any(value == tagName for tagName in tags)

	def getObjectKey(self, obj):
		try:
			return obj.windowHandle, obj.IA2UniqueID
		except:
			return id(obj)

	def getObjectAttribute(self, obj, attributeName):
		value = ''
		try:
			value = getattr(obj, attributeName, '') or ''
		except:
			pass

		if value:
			return str(value)

		try:
			return str(obj.IA2Attributes.get(attributeName, '') or '')
		except:
			return ''

	def getSubtitle(self):
		obj = self.main.subtitleContainer
		return self.getSubtitleText(obj)

	def getSubtitleText(self, obj):
		texts = []
		seenTexts = set()
		self.collectSubtitleText(obj, texts, seenTexts)
		if not texts:
			return ''
		return ' | \r\n'.join(texts) + ' | \r\n'

	def collectSubtitleText(self, obj, texts, seenTexts):
		for current in self.walkSubtree(obj, 120):
			text = self.getSubtitleObjectName(current)
			if text:
				if not self.isTimeControlObject(current, obj) and text not in seenTexts:
					texts.append(text)
					seenTexts.add(text)

	def isTimeControlObject(self, obj, subtitleContainer):
		current = obj
		limit = 20
		while current and limit > 0:
			limit -= 1
			value = (
				self.getObjectAttribute(current, 'class') + ' ' +
				self.getObjectAttribute(current, 'id')
			)
			if any(marker in value for marker in self.TIME_CONTROL_MARKERS):
				return True
			if self.getObjectKey(current) == self.getObjectKey(subtitleContainer):
				return False
			try:
				current = current.parent
			except:
				return False
		return False

	def getSubtitleObjectName(self, obj):
		try:
			text = obj.name or ''
		except:
			return ''

		text = text.replace(u'\u200b', '').strip()
		return text
