"""Domain exceptions used by numerical methods."""


class WeatherLabError(Exception):
    """Base exception for expected application errors."""


class ValidationError(WeatherLabError, ValueError):
    """Raised when numerical method inputs are invalid."""
