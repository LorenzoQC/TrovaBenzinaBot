from importlib import import_module

from trovabenzina.config import DEFAULT_LANGUAGE

_lang_modules = {
    "it": "trovabenzina.i18n.it",
    "en": "trovabenzina.i18n.en",
    "de": "trovabenzina.i18n.de",
    "fr": "trovabenzina.i18n.fr",
    "es": "trovabenzina.i18n.es",
    "ru": "trovabenzina.i18n.ru",
    "zh": "trovabenzina.i18n.zh",
    "ja": "trovabenzina.i18n.ja",
    "pt": "trovabenzina.i18n.pt",
    "ar": "trovabenzina.i18n.ar",
}
_translations = {}


def _load(lang: str):
    if lang not in _translations:
        mod = import_module(_lang_modules.get(lang, _lang_modules[DEFAULT_LANGUAGE]))
        _translations[lang] = getattr(mod, "TRANSLATIONS", {})
    return _translations[lang]


def t(key: str, lang: str | None = None, **kwargs) -> str:
    """
    Return the translated string for `key` in `lang`.
    Falls back to DEFAULT_LANGUAGE and, as a last resort, to the key itself.
    """
    lang = lang or DEFAULT_LANGUAGE
    trans = _load(lang).get(key)

    # first fallback: default language
    if not trans:
        trans = _load(DEFAULT_LANGUAGE).get(key)

    # second fallback: use the key itself
    if not trans:
        trans = key

    return trans.format(**kwargs)