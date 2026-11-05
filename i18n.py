#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""i18n.py - Internationalization (I18N) runtime architecture for ChatAndChess.

Provides multi-language support following Policy P-006 Tier-2:
Supported languages: German (de), English (en), Spanish (es),
Simplified Chinese (zh), Japanese (ja), Russian (ru).

4-level fallback hierarchy: target_lang -> en -> de -> key/default.
"""

import json
import locale
import os
import sys
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

# Defensive console UTF-8 encoding reconfiguration for Windows
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

SUPPORTED_LANGUAGES: List[str] = ["de", "en", "es", "zh", "ja", "ru"]
DEFAULT_LANGUAGE: str = "de"

LANGUAGE_NAMES: Dict[str, str] = {
    "de": "Deutsch",
    "en": "English",
    "es": "Español",
    "zh": "简体中文",
    "ja": "日本語",
    "ru": "Русский",
}

LANGUAGE_ALIASES: Dict[str, str] = {
    "german": "de",
    "deutsch": "de",
    "de-de": "de",
    "de_de": "de",
    "english": "en",
    "englisch": "en",
    "inglés": "en",
    "ingles": "en",
    "en-us": "en",
    "en_us": "en",
    "en-gb": "en",
    "en_gb": "en",
    "spanish": "es",
    "spanisch": "es",
    "español": "es",
    "espanol": "es",
    "es-es": "es",
    "es_es": "es",
    "chinese": "zh",
    "chinesisch": "zh",
    "chino": "zh",
    "zh-cn": "zh",
    "zh_cn": "zh",
    "japanese": "ja",
    "japanisch": "ja",
    "japonés": "ja",
    "japones": "ja",
    "ja-jp": "ja",
    "ja_jp": "ja",
    "russian": "ru",
    "russisch": "ru",
    "ruso": "ru",
    "ru-ru": "ru",
    "ru_ru": "ru",
}


def normalize_language_code(raw: Optional[str]) -> Optional[str]:
    """Normalize language code or alias to standard 2-letter code."""
    if not raw:
        return None
    code = raw.strip().lower().replace("_", "-")
    if code in SUPPORTED_LANGUAGES:
        return code
    if code in LANGUAGE_ALIASES:
        return LANGUAGE_ALIASES[code]
    prefix = code.split("-")[0]
    if prefix in SUPPORTED_LANGUAGES:
        return prefix
    if prefix in LANGUAGE_ALIASES:
        return LANGUAGE_ALIASES[prefix]
    return None


def detect_system_language() -> str:
    """Detect system language from environment variables or locale."""
    for var in ("CHATANDCHESS_LANG", "LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        val = os.environ.get(var)
        if val:
            for part in val.split(":"):
                norm = normalize_language_code(part)
                if norm:
                    return norm

    try:
        loc = locale.getlocale()[0]
        norm = normalize_language_code(loc)
        if norm:
            return norm
    except Exception:
        pass

    try:
        loc = locale.getdefaultlocale()[0]
        norm = normalize_language_code(loc)
        if norm:
            return norm
    except Exception:
        pass

    return DEFAULT_LANGUAGE


class TranslationManager:
    """Thread-safe translation manager with 4-level fallback hierarchy."""

    def __init__(
        self,
        locales_dir: Optional[Path] = None,
        default_lang: Optional[str] = None,
    ) -> None:
        self._lock = threading.RLock()
        self.locales_dir = locales_dir or (Path(__file__).resolve().parent / "locales")
        self.catalog_path = self.locales_dir / "translations.json"
        self._translations: Dict[str, Dict[str, str]] = {lang: {} for lang in SUPPORTED_LANGUAGES}
        self._current_language: str = default_lang or DEFAULT_LANGUAGE
        self.load_translations()

    def load_translations(self) -> None:
        """Load translations from catalog JSON."""
        with self._lock:
            if not self.catalog_path.is_file():
                return
            try:
                with open(self.catalog_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    for lang in SUPPORTED_LANGUAGES:
                        if lang in data and isinstance(data[lang], dict):
                            self._translations[lang] = {
                                str(k): str(v) for k, v in data[lang].items()
                            }
            except Exception as e:
                # Fallback to empty if file is corrupt or unreadable
                sys.stderr.write(f"[i18n] Error loading {self.catalog_path}: {e}\n")

    def set_language(self, lang_code: str) -> bool:
        """Set current language. Returns True if valid and set, False otherwise."""
        norm = normalize_language_code(lang_code)
        if norm in SUPPORTED_LANGUAGES:
            with self._lock:
                self._current_language = norm
            return True
        return False

    def get_language(self) -> str:
        """Get current 2-letter language code."""
        with self._lock:
            return self._current_language

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        return list(SUPPORTED_LANGUAGES)

    def get_language_name(self, lang_code: Optional[str] = None) -> str:
        """Get display name for a language code."""
        code = normalize_language_code(lang_code) or self.get_language()
        return LANGUAGE_NAMES.get(code, code)

    def get_fallback_chain(self, lang_code: Optional[str] = None) -> List[str]:
        """Compute the fallback chain: target -> en -> de."""
        target = normalize_language_code(lang_code) or self.get_language()
        chain = [target]
        if target != "en" and "en" not in chain:
            chain.append("en")
        if target != "de" and "de" not in chain:
            chain.append("de")
        return chain

    def t(self, key: str, default: Optional[str] = None, **kwargs: Any) -> str:
        """Translate a key using 4-tier fallback hierarchy with kwargs formatting."""
        with self._lock:
            chain = self.get_fallback_chain(self._current_language)
            template: Optional[str] = None

            for lang in chain:
                cat = self._translations.get(lang, {})
                if key in cat:
                    template = cat[key]
                    break

            if template is None:
                template = default if default is not None else key

            if not kwargs:
                return template

            try:
                return template.format(**kwargs)
            except Exception:
                return template

    def tr(self, key: str, default: Optional[str] = None, **kwargs: Any) -> str:
        """Alias for t()."""
        return self.t(key, default=default, **kwargs)


# Global singleton instance
_GLOBAL_MANAGER = TranslationManager()


def get_manager() -> TranslationManager:
    """Return the global TranslationManager instance."""
    return _GLOBAL_MANAGER


def set_language(lang_code: str) -> bool:
    """Set global active language."""
    return _GLOBAL_MANAGER.set_language(lang_code)


def get_language() -> str:
    """Get global active language."""
    return _GLOBAL_MANAGER.get_language()


def get_supported_languages() -> List[str]:
    """Get list of supported language codes."""
    return _GLOBAL_MANAGER.get_supported_languages()


def get_language_name(lang_code: Optional[str] = None) -> str:
    """Get language display name."""
    return _GLOBAL_MANAGER.get_language_name(lang_code)


def t(key: str, default: Optional[str] = None, **kwargs: Any) -> str:
    """Global translation helper."""
    return _GLOBAL_MANAGER.t(key, default=default, **kwargs)


def tr(key: str, default: Optional[str] = None, **kwargs: Any) -> str:
    """Global translation helper alias."""
    return _GLOBAL_MANAGER.tr(key, default=default, **kwargs)
