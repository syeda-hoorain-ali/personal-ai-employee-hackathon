"""
Error handling and retry logic for email operations.
"""
import time
import random
from typing import Callable, Any, Dict
from enum import Enum


class RetryStrategy(Enum):
    """Different strategies for retrying failed operations."""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIXED = "fixed"


class ErrorHandler:
    """
    Handles errors and implements retry logic for email operations.
    """
    def __init__(self):
        self.retry_attempts = 3
        self.initial_delay = 1  # seconds
        self.max_delay = 60  # seconds
        self.backoff_factor = 2

    def execute_with_retry(self, func: Callable, *args,
                          retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
                          exception_types: tuple = (Exception,),
                          **kwargs) -> Any:
        """
        Execute a function with retry logic.

        Args:
            func: Function to execute
            *args: Arguments to pass to the function
            retry_strategy: Strategy for calculating delays between retries
            exception_types: Types of exceptions to catch and retry
            **kwargs: Keyword arguments to pass to the function

        Returns:
            Result of the function call

        Raises:
            The original exception if retries are exhausted
        """
        last_exception = None

        for attempt in range(self.retry_attempts + 1):
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                last_exception = e

                if attempt == self.retry_attempts:
                    # Last attempt, raise the exception
                    break

                # Calculate delay based on strategy
                delay = self._calculate_delay(attempt, retry_strategy)

                # Add jitter to prevent thundering herd
                delay += random.uniform(0, 0.1 * delay)

                time.sleep(delay)

        raise last_exception

    def _calculate_delay(self, attempt: int, strategy: RetryStrategy) -> float:
        """
        Calculate delay based on retry strategy.

        Args:
            attempt: Current attempt number
            strategy: Retry strategy to use

        Returns:
            Delay in seconds
        """
        if strategy == RetryStrategy.FIXED:
            return self.initial_delay
        elif strategy == RetryStrategy.LINEAR:
            return self.initial_delay * (attempt + 1)
        elif strategy == RetryStrategy.EXPONENTIAL:
            delay = self.initial_delay * (self.backoff_factor ** attempt)
            return min(delay, self.max_delay)
        else:
            return self.initial_delay

    def handle_authentication_failure(self, provider: str) -> Dict[str, Any]:
        """
        Handle authentication failures for a provider.

        Args:
            provider: Name of the email provider

        Returns:
            Dictionary with error information
        """
        return {
            "error_code": "AUTH_ERROR",
            "message": f"Authentication failed for {provider}. Please check your credentials.",
            "recommendation": "Verify your account settings and re-authenticate"
        }

    def handle_provider_outage(self, provider: str) -> Dict[str, Any]:
        """
        Handle provider outages.

        Args:
            provider: Name of the email provider

        Returns:
            Dictionary with error information
        """
        return {
            "error_code": "PROVIDER_UNAVAILABLE",
            "message": f"The {provider} service is currently unavailable. Please try again later.",
            "retry_after": 300  # 5 minutes
        }

    def handle_quota_exceeded(self, resource_type: str) -> Dict[str, Any]:
        """
        Handle quota exceeded errors.

        Args:
            resource_type: Type of resource that exceeded quota

        Returns:
            Dictionary with error information
        """
        return {
            "error_code": "QUOTA_EXCEEDED",
            "message": f"Quota exceeded for {resource_type}. Please try again later.",
            "retry_after": 3600  # 1 hour
        }

    def classify_error(self, error: Exception) -> str:
        """
        Classify an error into a category.

        Args:
            error: Exception to classify

        Returns:
            Error category
        """
        error_str = str(error).lower()

        if any(keyword in error_str for keyword in ['auth', 'authenticate', 'credential', 'permission']):
            return 'AUTHENTICATION_ERROR'
        elif any(keyword in error_str for keyword in ['connection', 'timeout', 'network', 'offline']):
            return 'NETWORK_ERROR'
        elif any(keyword in error_str for keyword in ['quota', 'limit', 'exceeded', 'over quota']):
            return 'QUOTA_ERROR'
        elif any(keyword in error_str for keyword in ['not found', 'does not exist']):
            return 'NOT_FOUND_ERROR'
        else:
            return 'GENERAL_ERROR'


# Global error handler instance
error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """
    Get the global error handler instance.

    Returns:
        ErrorHandler instance
    """
    return error_handler


def execute_with_retry(func: Callable, *args,
                      retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
                      exception_types: tuple = (Exception,),
                      **kwargs) -> Any:
    """
    Execute a function with retry logic.

    Args:
        func: Function to execute
        *args: Arguments to pass to the function
        retry_strategy: Strategy for calculating delays between retries
        exception_types: Types of exceptions to catch and retry
        **kwargs: Keyword arguments to pass to the function

    Returns:
        Result of the function call
    """
    handler = get_error_handler()
    return handler.execute_with_retry(
        func,
        *args,
        retry_strategy=retry_strategy,
        exception_types=exception_types,
        **kwargs
    )


def handle_authentication_failure(provider: str) -> Dict[str, Any]:
    """
    Handle authentication failures for a provider.

    Args:
        provider: Name of the email provider

    Returns:
        Dictionary with error information
    """
    handler = get_error_handler()
    return handler.handle_authentication_failure(provider)


def handle_provider_outage(provider: str) -> Dict[str, Any]:
    """
    Handle provider outages.

    Args:
        provider: Name of the email provider

    Returns:
        Dictionary with error information
    """
    handler = get_error_handler()
    return handler.handle_provider_outage(provider)


def handle_quota_exceeded(resource_type: str) -> Dict[str, Any]:
    """
    Handle quota exceeded errors.

    Args:
        resource_type: Type of resource that exceeded quota

    Returns:
        Dictionary with error information
    """
    handler = get_error_handler()
    return handler.handle_quota_exceeded(resource_type)


def classify_error(error: Exception) -> str:
    """
    Classify an error into a category.

    Args:
        error: Exception to classify

    Returns:
        Error category
    """
    handler = get_error_handler()
    return handler.classify_error(error)
