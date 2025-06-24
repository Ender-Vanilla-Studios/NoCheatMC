def t(self, key, *args):
    text = self.TRANSLATIONS.get(key, key)
    return text.format(*args) if args else text