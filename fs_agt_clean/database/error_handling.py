"""
Error handling utilities for database operations.
"""

import asyncio
import functools
import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, cast

from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Type variables for function signatures
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


class DatabaseError(Exception):
    """Base exception for database errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        """Initialize the exception."""
        self.message = message
        self.original_error = original_error
        super().__init__(message)


class ConnectionError(DatabaseError):
    """Exception for database connection errors."""

    pass


class QueryError(DatabaseError):
    """Exception for database query errors."""

    pass


class TransactionError(DatabaseError):
    """Exception for database transaction errors."""

    pass


class IntegrityViolationError(DatabaseError):
    """Exception for database integrity violation errors."""

    pass


def map_exception(error: Exception) -> DatabaseError:
    """
    Map SQLAlchemy exceptions to our custom exceptions.

    Args:
        error: The original SQLAlchemy exception

    Returns:
        A custom database exception
    """
    if isinstance(error, IntegrityError):
        return IntegrityViolationError(
            f"Database integrity violation: {str(error)}", error
        )
    elif isinstance(error, OperationalError):
        return ConnectionError(f"Database connection error: {str(error)}", error)
    elif isinstance(error, DBAPIError):
        return QueryError(f"Database query error: {str(error)}", error)
    elif isinstance(error, SQLAlchemyError):
        return TransactionError(f"Database transaction error: {str(error)}", error)
    else:
        return DatabaseError(f"Unexpected database error: {str(error)}", error)


def with_retry(
    max_retries: int = 3,
    retry_delay: float = 0.5,
    backoff_factor: float = 2.0,
    retryable_errors: Optional[List[Type[Exception]]] = None,
) -> Callable[[F], F]:
    """
    Decorator for retrying database operations on transient errors.

    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries in seconds
        backoff_factor: Factor to increase delay between retries
        retryable_errors: List of exception types to retry on

    Returns:
        Decorated function
    """
    if retryable_errors is None:
        retryable_errors = [OperationalError, ConnectionError]

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error = None
            current_delay = retry_delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except tuple(retryable_errors) as e:
                    last_error = e
                    if attempt < max_retries:
                        logger.warning(
                            "Retryable error on attempt %s/%s: %s. Retrying in %.2f seconds...",
                            attempt + 1,
                            max_retries + 1,
                            str(e),
                            current_delay,
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(
                            "Operation failed after %s attempts: %s",
                            max_retries + 1,
                            str(e),
                        )
                except Exception as e:
                    # Non-retryable error
                    logger.error("Non-retryable error: %s", str(e))
                    raise map_exception(e)

            # If we get here, all retries failed
            if last_error:
                raise map_exception(last_error)
            else:
                raise DatabaseError("Operation failed for unknown reason")

        return cast(F, wrapper)

    return decorator


async def execute_with_retry(
    session: AsyncSession,
    operation: Callable[..., Any],
    *args: Any,
    max_retries: int = 3,
    retry_delay: float = 0.5,
    backoff_factor: float = 2.0,
    **kwargs: Any,
) -> Any:
    """
    Execute a database operation with retry logic.

    Args:
        session: The database session
        operation: The operation to execute
        *args: Arguments to pass to the operation
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries in seconds
        backoff_factor: Factor to increase delay between retries
        **kwargs: Keyword arguments to pass to the operation

    Returns:
        The result of the operation
    """
    last_error = None
    current_delay = retry_delay

    for attempt in range(max_retries + 1):
        try:
            return await operation(session, *args, **kwargs)
        except (OperationalError, ConnectionError) as e:
            last_error = e
            if attempt < max_retries:
                logger.warning(
                    "Retryable error on attempt %s/%s: %s. Retrying in %.2f seconds...",
                    attempt + 1,
                    max_retries + 1,
                    str(e),
                    current_delay,
                )
                await asyncio.sleep(current_delay)
                current_delay *= backoff_factor
            else:
                logger.error(
                    "Operation failed after %s attempts: %s",
                    max_retries + 1,
                    str(e),
                )
        except Exception as e:
            # Non-retryable error
            logger.error("Non-retryable error: %s", str(e))
            raise map_exception(e)

    # If we get here, all retries failed
    if last_error:
        raise map_exception(last_error)
    else:
        raise DatabaseError("Operation failed for unknown reason")


class TransactionMetrics:
    """Metrics for database transactions."""

    def __init__(self):
        """Initialize the metrics."""
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.operation_name: str = ""
        self.success: bool = False
        self.error: Optional[str] = None
        self.retries: int = 0

    def start(self, operation_name: str) -> None:
        """Start tracking a transaction."""
        self.start_time = time.time()
        self.operation_name = operation_name

    def end(self, success: bool, error: Optional[str] = None) -> None:
        """End tracking a transaction."""
        self.end_time = time.time()
        self.success = success
        self.error = error

    def increment_retry(self) -> None:
        """Increment the retry count."""
        self.retries += 1

    @property
    def duration(self) -> Optional[float]:
        """Get the transaction duration in seconds."""
        if self.start_time is not None and self.end_time is not None:
            return self.end_time - self.start_time
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the metrics to a dictionary."""
        return {
            "operation": self.operation_name,
            "success": self.success,
            "duration": self.duration,
            "error": self.error,
            "retries": self.retries,
            "timestamp": datetime.now().isoformat(),
        }


def with_metrics(operation_name: str) -> Callable[[F], F]:
    """
    Decorator for tracking database operation metrics.

    Args:
        operation_name: The name of the operation

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            metrics = TransactionMetrics()
            metrics.start(operation_name)

            try:
                result = await func(*args, **kwargs)
                metrics.end(True)
                return result
            except Exception as e:
                metrics.end(False, str(e))

                # Log metrics for failed operations
                logger.error(
                    "Database operation failed: %s",
                    metrics.to_dict(),
                )

                raise
            finally:
                # Record metrics (in a real implementation, this would send to a metrics service)
                if metrics.duration and metrics.duration > 1.0:
                    logger.warning(
                        "Slow database operation: %s took %.2f seconds",
                        operation_name,
                        metrics.duration,
                    )

        return cast(F, wrapper)

    return decorator


class TransactionContext:
    """Context manager for database transactions with error handling."""

    def __init__(
        self,
        session: AsyncSession,
        operation_name: str,
        max_retries: int = 3,
    ):
        """
        Initialize the transaction context.

        Args:
            session: The database session
            operation_name: The name of the operation
            max_retries: Maximum number of retry attempts
        """
        self.session = session
        self.operation_name = operation_name
        self.max_retries = max_retries
        self.metrics = TransactionMetrics()
        self.attempt = 0

    async def __aenter__(self) -> "TransactionContext":
        """Enter the transaction context."""
        self.metrics.start(self.operation_name)
        self.attempt += 1
        await self.session.begin()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> bool:
        """
        Exit the transaction context.

        Args:
            exc_type: The exception type, if any
            exc_val: The exception value, if any
            exc_tb: The exception traceback, if any

        Returns:
            True if the exception was handled, False otherwise
        """
        if exc_type is None:
            # No exception, commit the transaction
            try:
                await self.session.commit()
                self.metrics.end(True)
                return False  # Don't suppress any exceptions
            except Exception as e:
                logger.error("Error committing transaction: %s", str(e))
                await self.session.rollback()
                self.metrics.end(False, str(e))

                # Check if we should retry
                if self.attempt <= self.max_retries and isinstance(
                    e, (OperationalError, ConnectionError)
                ):
                    self.metrics.increment_retry()
                    logger.warning(
                        "Retrying transaction (attempt %s/%s): %s",
                        self.attempt,
                        self.max_retries,
                        self.operation_name,
                    )
                    return False  # Don't suppress the exception, let the retry logic handle it

                # Map the exception to our custom exception
                raise map_exception(e)
        else:
            # Exception occurred, rollback the transaction
            await self.session.rollback()
            self.metrics.end(False, str(exc_val))

            # Check if we should retry
            if self.attempt <= self.max_retries and issubclass(
                exc_type, (OperationalError, ConnectionError)
            ):
                self.metrics.increment_retry()
                logger.warning(
                    "Retrying transaction (attempt %s/%s): %s",
                    self.attempt,
                    self.max_retries,
                    self.operation_name,
                )
                return (
                    False  # Don't suppress the exception, let the retry logic handle it
                )

            # Log metrics for failed operations
            logger.error(
                "Transaction failed: %s",
                self.metrics.to_dict(),
            )

            return False  # Don't suppress the exception
