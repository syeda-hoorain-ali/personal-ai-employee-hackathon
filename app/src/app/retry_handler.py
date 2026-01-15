import time
import logging
from functools import wraps
from typing import Callable, Any, Optional


class TransientError(Exception):
    """Exception raised for transient errors that might resolve themselves."""
    pass


class PermanentError(Exception):
    """Exception raised for permanent errors that won't resolve."""
    pass


def with_retry(max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0,
               backoff_factor: float = 2.0,
               retry_on_exceptions: tuple = (TransientError, ConnectionError)):
    """
    Decorator to add retry logic to functions.

    Args:
        max_attempts: Maximum number of attempts (including initial)
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Factor by which delay increases after each attempt
        retry_on_exceptions: Tuple of exceptions to retry on
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except retry_on_exceptions as e:
                    last_exception = e

                    if attempt == max_attempts - 1:  # Last attempt
                        logging.error(f"All {max_attempts} attempts failed. Last error: {e}")
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (backoff_factor ** attempt), max_delay)

                    logging.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    time.sleep(delay)

            # This shouldn't be reached, but just in case
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


class RetryHandler:
    """
    A class-based approach to handling retries for more complex scenarios.
    """

    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0,
                 max_delay: float = 60.0, backoff_factor: float = 2.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.logger = logging.getLogger(self.__class__.__name__)

    def execute_with_retry(self, func: Callable, *args,
                          retry_on_exceptions: tuple = (TransientError, ConnectionError),
                          **kwargs) -> Any:
        """
        Execute a function with retry logic.

        Args:
            func: Function to execute
            *args: Arguments to pass to the function
            retry_on_exceptions: Tuple of exceptions to retry on
            **kwargs: Keyword arguments to pass to the function

        Returns:
            Result of the function call

        Raises:
            The last exception if all attempts fail
        """
        last_exception = None

        for attempt in range(self.max_attempts):
            try:
                result = func(*args, **kwargs)
                if attempt > 0:  # Log success after retries
                    self.logger.info(f"Function succeeded on attempt {attempt + 1}")
                return result
            except retry_on_exceptions as e:
                last_exception = e

                if attempt == self.max_attempts - 1:  # Last attempt
                    self.logger.error(
                        f"All {self.max_attempts} attempts failed. Last error: {e}"
                    )
                    raise

                # Calculate delay with exponential backoff
                delay = min(self.base_delay * (self.backoff_factor ** attempt), self.max_delay)

                self.logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {delay:.2f}s (attempt {attempt + 1}/{self.max_attempts})..."
                )

                time.sleep(delay)

        # This shouldn't be reached, but just in case
        if last_exception:
            raise last_exception

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt number."""
        return min(self.base_delay * (self.backoff_factor ** attempt), self.max_delay)


# Example usage functions
def example_usage():
    """Example of how to use the retry handler."""

    # Method 1: Using the decorator
    @with_retry(max_attempts=3, base_delay=1.0)
    def unreliable_function():
        import random
        if random.random() < 0.7:  # 70% chance of failure
            raise TransientError("Random failure occurred")
        return "Success!"

    # Method 2: Using the class
    retry_handler = RetryHandler(max_attempts=3, base_delay=1.0)

    def another_unreliable_function():
        import random
        if random.random() < 0.7:  # 70% chance of failure
            raise TransientError("Another random failure")
        return "Success!"

    # Execute with retry
    try:
        result = retry_handler.execute_with_retry(another_unreliable_function)
        print(f"Result: {result}")
    except Exception as e:
        print(f"All attempts failed: {e}")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Run example
    example_usage()
    