"""
Rate limiting functionality for the Email MCP Server.
"""
import time
from typing import Dict
from collections import defaultdict
import threading


class RateLimiter:
    """
    Simple rate limiter to prevent abuse of email operations.
    Implements a sliding window counter approach.
    """
    def __init__(self, max_requests: int = 10, window_size: int = 60):
        """
        Initialize the rate limiter.

        Args:
            max_requests: Maximum number of requests allowed in the window
            window_size: Size of the time window in seconds
        """
        self.max_requests = max_requests
        self.window_size = window_size
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = threading.Lock()

    def is_allowed(self, identifier: str) -> bool:
        """
        Check if a request from the given identifier is allowed.

        Args:
            identifier: Identifier for the requester (e.g., IP address, account ID)

        Returns:
            True if the request is allowed, False otherwise
        """
        with self.lock:
            current_time = time.time()

            # Clean old requests outside the window
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if current_time - req_time < self.window_size
            ]

            # Check if we're under the limit
            if len(self.requests[identifier]) < self.max_requests:
                self.requests[identifier].append(current_time)
                return True

            return False

    def get_reset_time(self, identifier: str) -> float:
        """
        Get the time when the rate limit will reset for the identifier.

        Args:
            identifier: Identifier for the requester

        Returns:
            Unix timestamp when the rate limit will reset
        """
        with self.lock:
            if identifier in self.requests and self.requests[identifier]:
                oldest_request = min(self.requests[identifier])
                return oldest_request + self.window_size
            return time.time()


# Global rate limiter instance
rate_limiter = RateLimiter(max_requests=10, window_size=60)


def get_rate_limiter() -> RateLimiter:
    """
    Get the global rate limiter instance.

    Returns:
        RateLimiter instance
    """
    return rate_limiter


def check_rate_limit(identifier: str) -> tuple[bool, dict]:
    """
    Check if a request is allowed based on rate limiting.

    Args:
        identifier: Identifier for the requester

    Returns:
        Tuple of (is_allowed, rate_limit_info)
    """
    limiter = get_rate_limiter()
    is_allowed = limiter.is_allowed(identifier)

    if not is_allowed:
        reset_time = limiter.get_reset_time(identifier)
        return False, {
            "error_code": "RATE_LIMIT_EXCEEDED",
            "message": "Rate limit exceeded. Please try again later.",
            "reset_time": reset_time
        }

    return True, {}
