// ==UserScript==
// @name         Crunchyroll Subtitle Reader (NVDA Bridge)
// @namespace    https://github.com/subtitle-reader
// @version      5.2
// @description  Intercepte les sous-titres de Crunchyroll pour NVDA Subtitle Reader
// @match        https://www.crunchyroll.com/*
// @match        https://beta.crunchyroll.com/*
// @grant        none
// @run-at       document-start
// ==/UserScript==

(function() {
	'use strict';

	var subtitleCues = [];
	var lastText = '';
	var bridgeEl = null;
	var currentUrl = location.href;
	var allSubtitleUrls = {};
	var lastDetectedLang = '';

	// === PARSER ASS ===
	function parseASS(assText) {
		var cues = [];
		var lines = assText.split('\n');
		var inEvents = false;
		var formatFields = [];

		for (var i = 0; i < lines.length; i++) {
			var line = lines[i].trim();
			if (line === '[Events]') { inEvents = true; continue; }
			if (line.match(/^\[.+\]$/)) { inEvents = false; continue; }
			if (!inEvents) continue;

			if (line.indexOf('Format:') === 0) {
				formatFields = line.substring(7).split(',').map(function(f) { return f.trim(); });
				continue;
			}

			if (line.indexOf('Dialogue:') !== 0) continue;

			var data = line.substring(9);
			var parts = [];
			var current = data;
			for (var s = 0; s < formatFields.length - 1; s++) {
				var commaIdx = current.indexOf(',');
				if (commaIdx === -1) break;
				parts.push(current.substring(0, commaIdx).trim());
				current = current.substring(commaIdx + 1);
			}
			parts.push(current);

			var startIdx = formatFields.indexOf('Start');
			var endIdx = formatFields.indexOf('End');
			var textIdx = formatFields.indexOf('Text');
			var styleIdx = formatFields.indexOf('Style');
			if (startIdx === -1 || endIdx === -1 || textIdx === -1) continue;

			var style = styleIdx !== -1 ? (parts[styleIdx] || '').toLowerCase() : '';
			if (style.indexOf('sign') !== -1 || style.indexOf('screen') !== -1 || style.indexOf('caption') !== -1) continue;

			var text = parts[textIdx].replace(/\{[^}]*\}/g, '').replace(/\\[Nn]/g, ' | ').replace(/\s+/g, ' ').trim();
			if (!text) continue;

			var startParts = parts[startIdx].split(':');
			var endParts = parts[endIdx].split(':');
			if (startParts.length !== 3 || endParts.length !== 3) continue;

			cues.push({
				start: toSeconds(startParts),
				end: toSeconds(endParts),
				text: text
			});
		}
		cues.sort(function(a, b) { return a.start - b.start; });
		return cues;
	}

	function toSeconds(parts) {
		var sec = parts[2].split('.');
		return parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseInt(sec[0]) + (sec.length > 1 ? parseInt(sec[1]) / 100 : 0);
	}

	// === CHARGEMENT DES SOUS-TITRES ===
	function loadSubtitle(lang) {
		if (!lang || !allSubtitleUrls[lang]) return;
		fetch(allSubtitleUrls[lang]).then(function(r) { return r.text(); }).then(function(text) {
			if (text.indexOf('[Events]') === -1) return;
			var cues = parseASS(text);
			if (cues.length > 0) {
				subtitleCues = cues;
				lastText = '';
				lastDetectedLang = lang;
				try { localStorage.setItem('nvda-cr-subtitle-lang', lang); } catch(e) {}
			}
		}).catch(function() {});
	}

	// === INTERCEPTION FETCH /playback/ ===
	var _origFetch = window.fetch;
	window.fetch = function() {
		var url = typeof arguments[0] === 'string' ? arguments[0] : (arguments[0] && arguments[0].url ? arguments[0].url : '');
		if (url.indexOf('/playback/') !== -1) {
			return _origFetch.apply(this, arguments).then(function(response) {
				var cloned = response.clone();
				cloned.json().then(function(data) {
					var subtitles = (data && data.subtitles) || (data && data.meta && data.meta.subtitles);
					if (!subtitles) return;
					allSubtitleUrls = {};
					var keys = Object.keys(subtitles);
					for (var i = 0; i < keys.length; i++) {
						if (subtitles[keys[i]] && subtitles[keys[i]].url) {
							allSubtitleUrls[keys[i]] = subtitles[keys[i]].url;
						}
					}
					if (keys.length > 0) waitForLangDetection();
				}).catch(function() {});
				return response;
			});
		}
		return _origFetch.apply(this, arguments);
	};

	// === DETECTION DE LANGUE ===
	var langDetectionTimer = null;

	function waitForLangDetection() {
		var attempts = 0;
		if (langDetectionTimer) clearInterval(langDetectionTimer);

		// Charger immediatement le fallback pour ne pas faire attendre
		var saved = null;
		try { saved = localStorage.getItem('nvda-cr-subtitle-lang'); } catch(e) {}
		if (saved && allSubtitleUrls[saved]) {
			loadSubtitle(saved);
		} else {
			var langs = Object.keys(allSubtitleUrls);
			if (langs.length > 0) loadSubtitle(langs[0]);
		}

		// Puis verifier le DOM pour corriger si la langue a change
		langDetectionTimer = setInterval(function() {
			attempts++;
			var lang = detectLangFromDOM();
			if (lang && allSubtitleUrls[lang]) {
				clearInterval(langDetectionTimer);
				langDetectionTimer = null;
				if (lang !== lastDetectedLang) loadSubtitle(lang);
				return;
			}
			if (attempts >= 10) {
				clearInterval(langDetectionTimer);
				langDetectionTimer = null;
			}
		}, 500);
	}

	var LANG_MAP = {
		'français': 'fr-FR', 'french': 'fr-FR', 'francais': 'fr-FR',
		'english': 'en-US', 'anglais': 'en-US',
		'deutsch': 'de-DE', 'german': 'de-DE', 'allemand': 'de-DE',
		'español (américa latina)': 'es-419',
		'español (españa)': 'es-ES', 'espagnol': 'es-ES',
		'italiano': 'it-IT', 'italien': 'it-IT',
		'português (brasil)': 'pt-BR', 'portugais': 'pt-BR',
		'русский': 'ru-RU', 'russe': 'ru-RU',
		'العربية': 'ar-SA', 'arabe': 'ar-SA',
		'bahasa indonesia': 'id-ID',
		'bahasa melayu': 'ms-MY',
		'tiếng việt': 'vi-VN',
		'ไทย': 'th-TH',
		'中文 (简体)': 'zh-CN',
		'中文 (繁体)': 'zh-HK',
		'日本語': 'ja-JP', 'japonais': 'ja-JP',
	};

	function textToLangCode(text) {
		if (!text) return null;
		text = text.toLowerCase().trim();
		if (LANG_MAP[text]) return LANG_MAP[text];
		var keys = Object.keys(LANG_MAP);
		for (var i = 0; i < keys.length; i++) {
			if (text.indexOf(keys[i]) !== -1) return LANG_MAP[keys[i]];
		}
		return null;
	}

	function detectLangFromDOM() {
		var player = document.getElementById('player-container');
		if (!player) return null;
		var selectors = '[aria-checked="true"], [aria-selected="true"], [data-selected="true"], [role="radio"][aria-checked="true"], [role="menuitemradio"][aria-checked="true"]';
		var candidates = player.querySelectorAll(selectors);
		for (var i = 0; i < candidates.length; i++) {
			var lang = textToLangCode(candidates[i].textContent);
			if (lang && allSubtitleUrls[lang]) return lang;
		}
		return null;
	}

	// === NAVIGATION SPA ===
	function checkNavigation() {
		if (location.href !== currentUrl) {
			currentUrl = location.href;
			subtitleCues = [];
			lastText = '';
			allSubtitleUrls = {};
			lastDetectedLang = '';
			bridgeEl = null;
		}
	}

	var _origPushState = history.pushState;
	var _origReplaceState = history.replaceState;
	history.pushState = function() { var r = _origPushState.apply(this, arguments); checkNavigation(); return r; };
	history.replaceState = function() { var r = _origReplaceState.apply(this, arguments); checkNavigation(); return r; };
	window.addEventListener('popstate', checkNavigation);

	// === BRIDGE NVDA ===
	function ensureBridge() {
		if (bridgeEl && bridgeEl.parentNode) return true;
		bridgeEl = document.getElementById('nvda-subtitle-bridge');
		if (bridgeEl) return true;

		var announcer = document.getElementById('player-accessibility-announcer');
		if (announcer) {
			bridgeEl = document.createElement('span');
			bridgeEl.id = 'nvda-subtitle-bridge';
			announcer.appendChild(bridgeEl);
			return true;
		}
		var player = document.getElementById('player-container');
		if (player) {
			bridgeEl = document.createElement('div');
			bridgeEl.id = 'nvda-subtitle-bridge';
			bridgeEl.style.cssText = 'position:absolute;opacity:0;pointer-events:none;';
			player.appendChild(bridgeEl);
			return true;
		}
		return false;
	}

	// === BOUCLE PRINCIPALE ===
	setInterval(function() {
		if (!ensureBridge()) return;
		if (subtitleCues.length === 0) return;
		var video = document.querySelector('video');
		if (!video) return;
		var t = video.currentTime;
		var texts = [];
		for (var i = 0; i < subtitleCues.length; i++) {
			if (subtitleCues[i].start <= t && subtitleCues[i].end >= t) texts.push(subtitleCues[i].text);
			if (subtitleCues[i].start > t + 1) break;
		}
		var text = texts.join(' | ');
		if (text !== lastText) {
			lastText = text;
			bridgeEl.textContent = text;
		}
	}, 150);

	// === OBSERVATEUR DE LANGUE ===
	function startLangObserver() {
		var player = document.getElementById('player-container');
		if (!player) { setTimeout(startLangObserver, 2000); return; }

		var debounceTimer = null;
		new MutationObserver(function() {
			if (debounceTimer) clearTimeout(debounceTimer);
			debounceTimer = setTimeout(function() {
				var lang = detectLangFromDOM();
				if (lang && lang !== lastDetectedLang && allSubtitleUrls[lang]) {
					loadSubtitle(lang);
				}
			}, 800);
		}).observe(player, {
			childList: true, subtree: true, attributes: true,
			attributeFilter: ['aria-checked', 'aria-selected', 'class', 'data-selected']
		});
	}

	setTimeout(startLangObserver, 3000);
})();
