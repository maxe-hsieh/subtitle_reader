#coding=utf-8

from .subtitle_alg import SubtitleAlg, SupportStatus
from .object_finder import find
from .compatible import role
from logHandler import log

class Adn(SubtitleAlg):
    info = {
        'name': 'Animation Digital Network',
        'url': 'https://animationdigitalnetwork.fr/',
        'status': SupportStatus.supported,
    }

    def getVideoPlayer(self):
        obj = self.main.focusObject
        # remonter jusqu'à l'élément avec la classe ADN contenant la vidéo
        videoPlayer = find(obj, 'parent', 'class', 'vjs-tech')
        return videoPlayer

    def getSubtitleContainer(self):
        videoPlayer = self.main.videoPlayer
        try:
            # on cherche le conteneur des sous-titres : class = vjs-text-track-display
            container = find(videoPlayer, 'next', 'class', 'vjs-text-track-display')
            if not container:
                log.debug("Sous-titres introuvables dans 'vjs-text-track-display'")
                return None
            return container
        except Exception as e:
            log.debug(f"Erreur ADN getSubtitleContainer : {e}")
            return None

    def getSubtitle(self):
        obj = self.main.subtitleContainer
        return super(Adn, self).getSubtitle(obj)
