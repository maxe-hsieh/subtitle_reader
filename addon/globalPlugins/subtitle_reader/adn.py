#coding=utf-8

# Imports de base de l'addon
from .subtitle_alg import SubtitleAlg, SupportStatus
from .object_finder import find
from .compatible import role
from logHandler import log

# Nouveaux imports pour la gestion du focus (aria-live) et des notifications
from comtypes import COMError
import time
import ui # Utile pour donner un retour à l'utilisateur, ex: "Lecture des sous-titres activée"

class Adn(SubtitleAlg):
    """
    Classe de support pour le site Animation Digital Network (ADN).
    Gère la recherche du lecteur, des sous-titres et la stabilisation du focus.
    """
    info = {
        'name': 'Animation Digital Network',
        'url': 'https://animationdigitalnetwork.fr/',
        'status': SupportStatus.supported,
    }

    # ===================================================================================
    # FONCTIONS DE DÉTECTION DES ÉLÉMENTS
    # ===================================================================================

    def _findMainPlayerContainer(self):
        """Trouve le conteneur principal du lecteur vidéo (classe 'video-js')."""
        obj = self.main.focusObject
        # On remonte dans l'arborescence à partir de l'objet actuel.
        player_container = find(obj, 'ancestor', 'class', 'video-js')
        if not player_container:
            # Si ça échoue, on tente une recherche globale.
            try:
                top_obj = obj.appModule.topLevelObject
                player_container = find(top_obj, 'descendant', 'class', 'video-js')
            except Exception as e:
                log.debug(f"Erreur lors de la recherche globale du conteneur du lecteur : {e}")
                player_container = None
        
        if not player_container:
            log.debug("ADN : Conteneur principal du lecteur introuvable.")
        return player_container

    def getVideoPlayer(self):
        """Trouve l'élément vidéo <video> lui-même (classe 'vjs-tech')."""
        main_container = self._findMainPlayerContainer()
        if main_container:
            videoPlayer = find(main_container, 'descendant', 'class', 'vjs-tech')
            if not videoPlayer:
                log.debug("ADN : Élément vidéo ('vjs-tech') introuvable dans le conteneur principal.")
            return videoPlayer
        return None

    def getSubtitleContainer(self):
        """Trouve le conteneur <div> des sous-titres (classe 'vjs-text-track-display')."""
        main_container = self._findMainPlayerContainer()
        if not main_container:
            log.debug("ADN : Conteneur de sous-titres non trouvé car conteneur principal absent.")
            return None
        
        try:
            container = find(main_container, 'descendant', 'class', 'vjs-text-track-display')
            if not container:
                log.debug("ADN : Conteneur de sous-titres ('vjs-text-track-display') introuvable.")
            return container
        except Exception as e:
            log.debug(f"Erreur ADN getSubtitleContainer : {e}")
            return None

    def getSubtitle(self):
        """Récupère le texte du sous-titre."""
        obj = self.main.subtitleContainer
        # La méthode de la classe parente se charge de récupérer le texte.
        return super(Adn, self).getSubtitle(obj)

    # ===================================================================================
    # NOUVELLE FONCTION POUR LA GESTION DU FOCUS
    # ===================================================================================

    def makeSubtitleContainerLive(self):
        """
        Rend le conteneur de sous-titres 'vivant' en utilisant ARIA.
        C'est la méthode recommandée pour que NVDA annonce les changements
        sans déplacer le focus de l'utilisateur.
        """
        log.debug("Tentative de rendre le conteneur de sous-titres 'live'")
        
        container = self.getSubtitleContainer()
        if not container:
            log.warning("ADN Focus: Impossible de trouver le conteneur pour le rendre 'live'.")
            return False

        try:
            # 1. VÉRIFICATION : Si c'est déjà fait, on ne fait rien.
            if container.IA2Attributes.get("live") in ("polite", "assertive"):
                log.info("ADN Focus: Le conteneur est déjà une région 'live'.")
                return True

            # 2. ACTION : On injecte du JavaScript pour ajouter l'attribut aria-live.
            log.info("ADN Focus: Injection du script 'aria-live=assertive'...")
            container.executeScript("this.setAttribute('aria-live', 'assertive');")
            
            # 3. PAUSE : On laisse 0.1s au navigateur et à NVDA pour traiter le changement.
            time.sleep(0.1) 
            
            # 4. CONFIRMATION : On vérifie que NVDA voit bien le nouvel attribut.
            if container.IA2Attributes.get("live") == "assertive":
                log.info("✅ SUCCÈS : Le conteneur est maintenant une région 'live'.")
                ui.message("Lecture des sous-titres activée") # Notifie l'utilisateur
                return True
            else:
                log.error("❌ ÉCHEC : L'attribut 'aria-live' a été injecté mais n'est pas détecté.")
                return False

        except (COMError, RuntimeError) as e:
            log.error(f"ADN Focus: Erreur technique lors de l'injection du script : {e}")
            return False