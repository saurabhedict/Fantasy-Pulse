"""Domain-level errors, mapped to HTTP responses in main.py."""


class AppError(Exception):
    status_code = 400


class MatchNotFound(AppError):
    status_code = 404


class InvalidTeam(AppError):
    status_code = 422


class StepOutOfRange(AppError):
    status_code = 422


class LLMUnavailable(AppError):
    status_code = 503
