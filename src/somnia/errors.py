"""Public Somnia exception hierarchy."""


class SomniaError(Exception):
    pass


class ObjectModelError(SomniaError):
    pass


class NativeLibraryError(SomniaError):
    pass


class EmbeddedRuntimeError(SomniaError):
    pass
