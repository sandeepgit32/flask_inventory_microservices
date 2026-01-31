"""
Circuit Breaker Pattern Implementation

Prevents cascading failures by monitoring service call failures
and temporarily blocking calls when failure threshold is reached.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Failure threshold reached, requests fail immediately
- HALF_OPEN: Test request allowed after timeout period
"""

import time
import logging
from enum import Enum
from threading import Lock
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is in OPEN state"""
    pass


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.
    
    Args:
        failure_threshold: Number of failures before opening circuit (default: 5)
        timeout: Seconds to wait before attempting HALF_OPEN state (default: 30)
        name: Name identifier for this circuit breaker
    """
    
    def __init__(self, failure_threshold=5, timeout=30, name="default"):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.name = name
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.lock = Lock()
        
    def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result of func execution
            
        Raises:
            CircuitBreakerOpenError: If circuit is OPEN
            Exception: Any exception raised by func
        """
        with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit breaker '{self.name}' moved to HALF_OPEN state")
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Try again after {self.timeout} seconds."
                    )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self):
        """Check if enough time has passed to attempt a reset"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.timeout
    
    def _on_success(self):
        """Handle successful call"""
        with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                logger.info(f"Circuit breaker '{self.name}' moved to CLOSED state")
            self.failure_count = 0
            self.last_failure_time = None
    
    def _on_failure(self):
        """Handle failed call"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker '{self.name}' moved back to OPEN state "
                    f"after failed test request"
                )
            elif self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error(
                    f"Circuit breaker '{self.name}' moved to OPEN state "
                    f"after {self.failure_count} failures"
                )
    
    def reset(self):
        """Manually reset the circuit breaker to CLOSED state"""
        with self.lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
            logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED state")
    
    def get_state(self):
        """Get current circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time
        }


def circuit_breaker(failure_threshold=5, timeout=30, name="default"):
    """
    Decorator for applying circuit breaker pattern to functions.
    
    Args:
        failure_threshold: Number of failures before opening circuit
        timeout: Seconds to wait before attempting HALF_OPEN state
        name: Name identifier for this circuit breaker
        
    Example:
        @circuit_breaker(failure_threshold=3, timeout=60, name="external_api")
        def call_external_api():
            # API call logic
            pass
    """
    breaker = CircuitBreaker(failure_threshold, timeout, name)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        wrapper.breaker = breaker  # Attach breaker for external access
        return wrapper
    
    return decorator
