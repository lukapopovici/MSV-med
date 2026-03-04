class PacsError(Exception):
    pass

class PacsConnectionError(PacsError):
    pass

class PacsDataError(PacsError):
    pass

class PacsAuthenticationError(PacsError):
    pass