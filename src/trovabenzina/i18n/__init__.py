from importlib import import_module

from trovabenzina.config import DEFAULT_LANGUAGE

_lang_modules = {
    "it": "trovabenzina.i18n.it",
    "en": "trovabenzina.i18n.en",
}
_translations = {}


def _load(lang: str):
    if lang not in _translations:
        mod = import_module(_lang_modules.get(lang, _lang_modules[DEFAULT_LANGUAGE]))
        _translations[lang] = getattr(mod, "TRANSLATIONS", {})
    return _translations[lang]


def t(key: str, lang: str = None, **kwargs) -> str:
    """
    Restituisce la stringa tradotta per `key` in `lang`,
    con fallback a DEFAULT_LANGUAGE e formattazione with **kwargs.
    """
    lang = lang or DEFAULT_LANGUAGE
    trans = _load(lang).get(key)
    if trans is None:
        # fallback ultima risorsa
        trans = _load(DEFAULT_LANGUAGE).get(key, "")
    return trans.format(**kwargs)
