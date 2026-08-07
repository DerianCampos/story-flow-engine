import backoff
from typing import Tuple, Type

from src.app.shared.global_variables import MAX_ERROR_RETRIES
from src.app.shared.log_config import get_logger

log = get_logger(__name__)

def retry_on_exception(max_tries=MAX_ERROR_RETRIES):
    """
    Reusable decorator for retrying a function with backoff on exceptions.

    Args:
        max_tries (int): Maximum number of attempts before giving up.

    Returns:
        callable: A decorator function wrapping the retry logic.
    """
    return backoff.on_exception(
        backoff.expo,  # Exponential backoff
        Exception,  # Retry on any exception
        max_tries=max_tries,  # Maximum number of attempts
        on_backoff=lambda details: log.warning(f"Retrying due to: {details['exception']}"),
        on_giveup=lambda details: log.error(f"Giving up after {details['tries']} attempts.")
    )


def retry_read_operation(max_tries: int = None, backoff_factor: float = None,
                         exceptions: Tuple[Type[Exception], ...] = None):
    """
    Decorator for retrying read operations with configurable parameters.
    
    Args:
        max_tries (int): Maximum number of attempts before giving up.
        backoff_factor (float): Backoff factor for exponential backoff.
        exceptions (Tuple[Type[Exception], ...]): Exception types to retry on.
    
    Returns:
        callable: A decorator function wrapping the retry logic for read operations.
    """

    if max_tries is None:
        max_tries = 3
    if backoff_factor is None:
        backoff_factor = 1.5
    if exceptions is None:
        from sqlalchemy.exc import SQLAlchemyError, OperationalError
        exceptions = (SQLAlchemyError, OperationalError, TimeoutError)

    return backoff.on_exception(
        backoff.expo,
        exceptions,
        max_tries=max_tries,
        factor=backoff_factor,
        on_backoff=lambda details: log.warning(f"Read operation retry due to: {details['exception']}"),
        on_giveup=lambda details: log.error(f"Read operation failed after {details['tries']} attempts.")
    )


def retry_write_operation(max_tries: int = None, backoff_factor: float = None,
                          exceptions: Tuple[Type[Exception], ...] = None):
    """
    Decorator for retrying write operations with configurable parameters.
    
    Args:
        max_tries (int): Maximum number of attempts before giving up.
        backoff_factor (float): Backoff factor for exponential backoff.
        exceptions (Tuple[Type[Exception], ...]): Exception types to retry on.
    
    Returns:
        callable: A decorator function wrapping the retry logic for write operations.
    """

    if max_tries is None:
        max_tries = 5
    if backoff_factor is None:
        backoff_factor = 2.0
    if exceptions is None:
        from sqlalchemy.exc import SQLAlchemyError, OperationalError, IntegrityError
        exceptions = (SQLAlchemyError, OperationalError, IntegrityError)

    return backoff.on_exception(
        backoff.expo,
        exceptions,
        max_tries=max_tries,
        factor=backoff_factor,
        on_backoff=lambda details: log.warning(f"Write operation retry due to: {details['exception']}"),
        on_giveup=lambda details: log.error(f"Write operation failed after {details['tries']} attempts.")
    )


def retry_critical_operation(max_tries: int = None, backoff_factor: float = None,
                             exceptions: Tuple[Type[Exception], ...] = None):
    """
    Decorator for retrying critical operations with configurable parameters.
    
    Args:
        max_tries (int): Maximum number of attempts before giving up.
        backoff_factor (float): Backoff factor for exponential backoff.
        exceptions (Tuple[Type[Exception], ...]): Exception types to retry on.
    
    Returns:
        callable: A decorator function wrapping the retry logic for critical operations.
    """

    if max_tries is None:
        max_tries = 7
    if backoff_factor is None:
        backoff_factor = 2.5
    if exceptions is None:
        exceptions = (Exception,)

    return backoff.on_exception(
        backoff.expo,
        exceptions,
        max_tries=max_tries,
        factor=backoff_factor,
        on_backoff=lambda details: log.warning(f"Critical operation retry due to: {details['exception']}"),
        on_giveup=lambda details: log.error(f"Critical operation failed after {details['tries']} attempts.")
    )
