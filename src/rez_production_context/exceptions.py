"""Module exceptions."""

class EntityNotFoundError(LookupError):
    """Raised by a connector when a requested entity does not exist in the remote database."""