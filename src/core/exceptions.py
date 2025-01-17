class AuthenticationError(Exception):
    """Base class for authentication related errors"""

    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid"""

    pass


class TokenExpiredError(AuthenticationError):
    """Raised when token has expired"""

    pass


class TokenInvalidError(AuthenticationError):
    """Raised when token is invalid"""

    pass


class UserNotFoundError(AuthenticationError):
    """Raised when user is not found"""

    pass


class AuthorizationError(Exception):
    """Base class for authorization related errors"""

    pass


class InsufficientPermissionsError(AuthorizationError):
    """Raised when user doesn't have required permissions"""

    pass


def register_error_handlers(app):
    @app.errorhandler(AuthenticationError)
    def handle_authentication_error(error):
        return {"error": error.__class__.__name__, "message": str(error)}, 401

    @app.errorhandler(AuthorizationError)
    def handle_authorization_error(error):
        return {"error": error.__class__.__name__, "message": str(error)}, 403

    @app.errorhandler(404)
    def handle_not_found(error):
        return {
            "error": "NotFoundError",
            "message": "The requested resource was not found",
        }, 404

    @app.errorhandler(Exception)
    def handle_generic_error(error):
        # Log the error here
        return {
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
        }, 500
