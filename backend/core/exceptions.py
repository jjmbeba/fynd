class FyndError(Exception):
    """Base for all application errors."""

    pass


class DomainError(FyndError):
    """Business rule violation — maps to 4xx."""

    pass


class InfrastructureError(FyndError):
    """External system failure — maps to 5xx."""

    pass
