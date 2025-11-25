class AuthenticationError(Exception):
    pass

class AuthorizationError(Exception):
    pass

class UserNotFoundError(Exception):
    pass

class UserAlreadyExistsError(Exception):
    pass