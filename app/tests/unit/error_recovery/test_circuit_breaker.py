"""
Tests for circuit breaker pattern implementation.

This module tests the CircuitBreaker class including state transitions,
failure threshold behavior, timeout recovery, state persistence, and
dashboard integration.
"""

import pytest
import time
from pathlib import Path
from datetime import datetime, UTC, timedelta
from unittest.mock import Mock, patch

from app.error_recovery.circuit_breaker import CircuitBreaker, with_circuit_breaker
from app.error_recovery.entities import CircuitBreakerState, ComponentStatus, ErrorType
from app.error_recovery.exceptions import CircuitBreakerOpenError, AuthenticationError
from app.error_recovery.error_logger import ErrorLogger
from app.error_recovery.utils import read_json_file


class TestCircuitBreakerInitialization:
    """Test circuit breaker initialization."""

    def test_init_default_state(self, tmp_path):
        """Test circuit breaker initializes in CLOSED state."""
        cb = CircuitBreaker(
            component="TestComponent",
            health_status_path=tmp_path / "health_status.json"
        )

        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0
        assert cb.last_failure_time is None
        assert cb.last_success_time is None

    def test_init_with_custom_thresholds(self, tmp_path):
        """Test circuit breaker with custom failure threshold and timeout."""
        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=5,
            timeout_seconds=120,
            health_status_path=tmp_path / "health_status.json"
        )

        assert cb.failure_threshold == 5
        assert cb.timeout_seconds == 120

    def test_init_loads_persisted_state(self, tmp_path):
        """Test circuit breaker loads state from persistence file."""
        health_status_path = tmp_path / "health_status.json"

        # Create persisted state
        persisted_state = {
            "TestComponent": {
                "state": "OPEN",
                "failure_count": 4,
                "last_failure_time": "2024-01-01T12:00:00Z",
                "last_success_time": None
            }
        }

        import json
        with open(health_status_path, 'w') as f:
            json.dump(persisted_state, f)

        # Initialize circuit breaker
        cb = CircuitBreaker(
            component="TestComponent",
            health_status_path=health_status_path
        )

        assert cb.state == CircuitBreakerState.OPEN
        assert cb.failure_count == 4
        assert cb.last_failure_time == "2024-01-01T12:00:00Z"


class TestCircuitBreakerStateTransitions:
    """Test circuit breaker state transitions (T057)."""

    def test_closed_to_open_on_threshold(self, tmp_path):
        """Test circuit transitions from CLOSED to OPEN after failure threshold."""
        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=3,
            health_status_path=tmp_path / "health_status.json"
        )

        def failing_function():
            raise Exception("Test failure")

        # First two failures should keep circuit closed
        for i in range(2):
            with pytest.raises(Exception):
                cb.call(failing_function)
            assert cb.state == CircuitBreakerState.CLOSED
            assert cb.failure_count == i + 1

        # Third failure should open the circuit
        with pytest.raises(Exception):
            cb.call(failing_function)

        assert cb.state == CircuitBreakerState.OPEN
        assert cb.failure_count == 3

    def test_open_blocks_requests(self, tmp_path):
        """Test OPEN circuit blocks all requests."""
        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=2,
            health_status_path=tmp_path / "health_status.json"
        )

        def failing_function():
            raise Exception("Test failure")

        # Trigger circuit to open
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(failing_function)

        assert cb.state == CircuitBreakerState.OPEN

        # Next call should be blocked
        with pytest.raises(CircuitBreakerOpenError) as exc_info:
            cb.call(lambda: "success")

        assert "Circuit breaker is OPEN" in str(exc_info.value)
        assert "TestComponent" in str(exc_info.value)

    def test_open_to_half_open_after_timeout(self, tmp_path):
        """Test circuit transitions from OPEN to HALF_OPEN after timeout."""
        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=2,
            timeout_seconds=1,  # Short timeout for testing
            health_status_path=tmp_path / "health_status.json"
        )

        def failing_function():
            raise Exception("Test failure")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(failing_function)

        assert cb.state == CircuitBreakerState.OPEN

        # Wait for timeout
        time.sleep(1.1)

        # Next call should transition to HALF_OPEN
        def successful_function():
            return "success"

        result = cb.call(successful_function)

        assert result == "success"
        assert cb.state == CircuitBreakerState.CLOSED  # Success closes circuit

    def test_half_open_to_closed_on_success(self, tmp_path):
        """Test circuit transitions from HALF_OPEN to CLOSED on success."""
        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=2,
            timeout_seconds=1,
            health_status_path=tmp_path / "health_status.json"
        )

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))

        # Wait for timeout and manually transition to HALF_OPEN
        time.sleep(1.1)
        cb.state = CircuitBreakerState.HALF_OPEN
        cb._save_state()

        # Successful call should close circuit
        result = cb.call(lambda: "success")

        assert result == "success"
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0

    def test_half_open_to_open_on_failure(self, tmp_path):
        """Test circuit transitions from HALF_OPEN to OPEN on failure."""
        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=3,
            timeout_seconds=1,
            health_status_path=tmp_path / "health_status.json"
        )

        # Open the circuit
        for _ in range(3):
            with pytest.raises(Exception):
                cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))

        # Wait for timeout and manually transition to HALF_OPEN
        time.sleep(1.1)
        cb.state = CircuitBreakerState.HALF_OPEN
        cb._save_state()

        # Failure in HALF_OPEN should immediately open circuit
        with pytest.raises(Exception):
            cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))

        assert cb.state == CircuitBreakerState.OPEN


class TestCircuitBreakerFailureThreshold:
    """Test failure threshold behavior (T058)."""

    def test_failure_count_increments(self, tmp_path):
        """Test failure count increments on each failure."""
        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=5,
            health_status_path=tmp_path / "health_status.json"
        )

        for i in range(4):
            with pytest.raises(Exception):
                cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))
            assert cb.failure_count == i + 1
            assert cb.state == CircuitBreakerState.CLOSED

    def test_failure_count_resets_on_success(self, tmp_path):
        """Test failure count resets to 0 on successful call."""
        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=5,
            health_status_path=tmp_path / "health_status.json"
        )

        # Accumulate some failures
        for _ in range(3):
            with pytest.raises(Exception):
                cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))

        assert cb.failure_count == 3

        # Successful call should reset count
        result = cb.call(lambda: "success")

        assert result == "success"
        assert cb.failure_count == 0
        assert cb.state == CircuitBreakerState.CLOSED

    def test_custom_failure_threshold(self, tmp_path):
        """Test circuit opens at custom failure threshold."""
        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=10,
            health_status_path=tmp_path / "health_status.json"
        )

        # Should stay closed for 9 failures
        for i in range(9):
            with pytest.raises(Exception):
                cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))
            assert cb.state == CircuitBreakerState.CLOSED

        # 10th failure should open circuit
        with pytest.raises(Exception):
            cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))

        assert cb.state == CircuitBreakerState.OPEN
        assert cb.failure_count == 10


class TestCircuitBreakerTimeout:
    """Test timeout and recovery attempts (T059)."""

    def test_timeout_allows_recovery_attempt(self, tmp_path):
        """Test circuit allows recovery attempt after timeout."""
        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=2,
            timeout_seconds=1,
            health_status_path=tmp_path / "health_status.json"
        )

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))

        assert cb.state == CircuitBreakerState.OPEN

        # Immediate call should be blocked
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "success")

        # Wait for timeout
        time.sleep(1.1)

        # Should allow recovery attempt
        result = cb.call(lambda: "success")
        assert result == "success"
        assert cb.state == CircuitBreakerState.CLOSED

    def test_timeout_not_elapsed_blocks_requests(self, tmp_path):
        """Test circuit blocks requests before timeout elapses."""
        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=2,
            timeout_seconds=10,  # Long timeout
            health_status_path=tmp_path / "health_status.json"
        )

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))

        # Should still be blocked
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "success")

    def test_custom_timeout_duration(self, tmp_path):
        """Test circuit respects custom timeout duration."""
        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=2,
            timeout_seconds=2,
            health_status_path=tmp_path / "health_status.json"
        )

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))

        # Wait less than timeout
        time.sleep(1)
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "success")

        # Wait for full timeout
        time.sleep(1.1)
        result = cb.call(lambda: "success")
        assert result == "success"


class TestCircuitBreakerPersistence:
    """Test state persistence to health_status.json (T060)."""

    def test_state_persisted_on_failure(self, tmp_path):
        """Test circuit breaker state is persisted after failure."""
        health_status_path = tmp_path / "health_status.json"

        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=2,
            health_status_path=health_status_path
        )

        # Trigger a failure
        with pytest.raises(Exception):
            cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))

        # Check persisted state
        data = read_json_file(health_status_path)
        assert "TestComponent" in data
        assert data["TestComponent"]["state"] == "CLOSED"
        assert data["TestComponent"]["failure_count"] == 1

    def test_state_persisted_on_open(self, tmp_path):
        """Test circuit breaker state is persisted when opening."""
        health_status_path = tmp_path / "health_status.json"

        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=2,
            health_status_path=health_status_path
        )

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))

        # Check persisted state
        data = read_json_file(health_status_path)
        assert data["TestComponent"]["state"] == "OPEN"
        assert data["TestComponent"]["failure_count"] == 2
        assert data["TestComponent"]["last_failure_time"] is not None

    def test_state_persisted_on_success(self, tmp_path):
        """Test circuit breaker state is persisted after success."""
        health_status_path = tmp_path / "health_status.json"

        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=2,
            health_status_path=health_status_path
        )

        # Successful call
        result = cb.call(lambda: "success")

        # Check persisted state
        data = read_json_file(health_status_path)
        assert data["TestComponent"]["state"] == "CLOSED"
        assert data["TestComponent"]["failure_count"] == 0
        assert data["TestComponent"]["last_success_time"] is not None

    def test_multiple_components_persisted(self, tmp_path):
        """Test multiple circuit breakers persist to same file."""
        health_status_path = tmp_path / "health_status.json"

        cb1 = CircuitBreaker(
            component="Component1",
            health_status_path=health_status_path
        )
        cb2 = CircuitBreaker(
            component="Component2",
            health_status_path=health_status_path
        )

        # Trigger different states
        cb1.call(lambda: "success")

        with pytest.raises(Exception):
            cb2.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))

        # Check both components persisted
        data = read_json_file(health_status_path)
        assert "Component1" in data
        assert "Component2" in data
        assert data["Component1"]["state"] == "CLOSED"
        assert data["Component2"]["state"] == "CLOSED"


class TestCircuitBreakerDashboardIntegration:
    """Test dashboard integration with paused components (T061)."""

    def test_dashboard_updated_on_open(self, tmp_path):
        """Test dashboard shows paused component when circuit opens."""
        logs_dir = tmp_path / "logs"
        dashboard_path = tmp_path / "dashboard.json"
        health_status_path = tmp_path / "health_status.json"

        error_logger = ErrorLogger(logs_dir, dashboard_path)

        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=2,
            health_status_path=health_status_path,
            error_logger=error_logger
        )

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))

        # Check dashboard
        dashboard = read_json_file(dashboard_path)
        assert "paused_components" in dashboard
        assert "TestComponent" in dashboard["paused_components"]
        assert dashboard["paused_components"]["TestComponent"]["failure_count"] == 2

    def test_dashboard_updated_on_close(self, tmp_path):
        """Test dashboard removes paused component when circuit closes."""
        logs_dir = tmp_path / "logs"
        dashboard_path = tmp_path / "dashboard.json"
        health_status_path = tmp_path / "health_status.json"

        error_logger = ErrorLogger(logs_dir, dashboard_path)

        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=2,
            timeout_seconds=1,
            health_status_path=health_status_path,
            error_logger=error_logger
        )

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))

        # Wait and recover
        time.sleep(1.1)
        cb.call(lambda: "success")

        # Check dashboard
        dashboard = read_json_file(dashboard_path)
        assert "TestComponent" not in dashboard.get("paused_components", {})

    def test_dashboard_shows_half_open_state(self, tmp_path):
        """Test dashboard shows component in HALF_OPEN state."""
        logs_dir = tmp_path / "logs"
        dashboard_path = tmp_path / "dashboard.json"
        health_status_path = tmp_path / "health_status.json"

        error_logger = ErrorLogger(logs_dir, dashboard_path)

        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=2,
            timeout_seconds=1,
            health_status_path=health_status_path,
            error_logger=error_logger
        )

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))

        # Wait for timeout to trigger HALF_OPEN
        time.sleep(1.1)

        # Manually check state before recovery attempt
        assert cb._should_attempt_reset()

        # Dashboard should still show paused during HALF_OPEN
        dashboard = read_json_file(dashboard_path)
        assert "TestComponent" in dashboard.get("paused_components", {})


class TestCircuitBreakerDecorator:
    """Test with_circuit_breaker decorator."""

    def test_decorator_wraps_function(self, tmp_path):
        """Test decorator properly wraps function."""
        @with_circuit_breaker(
            component="TestComponent",
            failure_threshold=2,
            health_status_path=tmp_path / "health_status.json"
        )
        def test_function(x):
            return x * 2

        result = test_function(5)
        assert result == 10

    def test_decorator_opens_on_failures(self, tmp_path):
        """Test decorator opens circuit after failures."""
        @with_circuit_breaker(
            component="TestComponent",
            failure_threshold=2,
            health_status_path=tmp_path / "health_status.json"
        )
        def failing_function():
            raise Exception("Test failure")

        # Trigger failures
        for _ in range(2):
            with pytest.raises(Exception):
                failing_function()

        # Next call should be blocked
        with pytest.raises(CircuitBreakerOpenError):
            failing_function()


class TestCircuitBreakerGetStatus:
    """Test get_status method."""

    def test_get_status_closed(self, tmp_path):
        """Test get_status returns RUNNING when circuit is CLOSED."""
        cb = CircuitBreaker(
            component="TestComponent",
            health_status_path=tmp_path / "health_status.json"
        )

        status = cb.get_status()

        assert status.component == "TestComponent"
        assert status.status == ComponentStatus.RUNNING
        assert status.circuit_breaker_state == CircuitBreakerState.CLOSED
        assert status.failure_count == 0

    def test_get_status_open(self, tmp_path):
        """Test get_status returns PAUSED when circuit is OPEN."""
        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=2,
            health_status_path=tmp_path / "health_status.json"
        )

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))

        status = cb.get_status()

        assert status.status == ComponentStatus.PAUSED
        assert status.circuit_breaker_state == CircuitBreakerState.OPEN
        assert status.failure_count == 2

    def test_get_status_half_open(self, tmp_path):
        """Test get_status returns STARTING when circuit is HALF_OPEN."""
        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=2,
            timeout_seconds=1,
            health_status_path=tmp_path / "health_status.json"
        )

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))

        # Wait and transition to HALF_OPEN
        time.sleep(1.1)
        cb.state = CircuitBreakerState.HALF_OPEN

        status = cb.get_status()

        assert status.status == ComponentStatus.STARTING
        assert status.circuit_breaker_state == CircuitBreakerState.HALF_OPEN


class TestCircuitBreakerReset:
    """Test manual reset functionality."""

    def test_manual_reset_closes_circuit(self, tmp_path):
        """Test manual reset closes an open circuit."""
        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=2,
            health_status_path=tmp_path / "health_status.json"
        )

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))

        assert cb.state == CircuitBreakerState.OPEN

        # Manual reset
        cb.reset()

        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0
        assert cb.last_success_time is not None

    def test_manual_reset_persists_state(self, tmp_path):
        """Test manual reset persists new state."""
        health_status_path = tmp_path / "health_status.json"

        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=2,
            health_status_path=health_status_path
        )

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(lambda: (_ for _ in ()).throw(Exception("Test failure")))

        # Manual reset
        cb.reset()

        # Check persisted state
        data = read_json_file(health_status_path)
        assert data["TestComponent"]["state"] == "CLOSED"
        assert data["TestComponent"]["failure_count"] == 0


class TestAuthenticationErrorCircuitBreaker:
    """Test circuit breaker authentication error handling (Phase 6 - T067)."""

    def test_circuit_opens_immediately_on_auth_error(self, tmp_path):
        """Test circuit opens immediately on authentication error without waiting for threshold."""
        logs_dir = tmp_path / "logs"
        dashboard_path = tmp_path / "dashboard.json"
        health_status_path = tmp_path / "health_status.json"

        error_logger = ErrorLogger(logs_dir, dashboard_path)

        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=4,  # High threshold
            health_status_path=health_status_path,
            error_logger=error_logger
        )

        # Single authentication error should open circuit immediately
        with pytest.raises(AuthenticationError):
            cb.call(lambda: (_ for _ in ()).throw(AuthenticationError("TestComponent", "Invalid credentials")))

        # Circuit should be open after just one auth error
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.failure_count == 1

        # Next call should be blocked
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "success")

    def test_auth_error_updates_dashboard(self, tmp_path):
        """Test authentication error updates dashboard with action required."""
        logs_dir = tmp_path / "logs"
        dashboard_path = tmp_path / "dashboard.json"
        health_status_path = tmp_path / "health_status.json"

        error_logger = ErrorLogger(logs_dir, dashboard_path)

        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=4,
            health_status_path=health_status_path,
            error_logger=error_logger
        )

        # Trigger authentication error
        with pytest.raises(AuthenticationError):
            cb.call(lambda: (_ for _ in ()).throw(AuthenticationError("TestComponent", "Invalid credentials")))

        # Check dashboard
        dashboard = read_json_file(dashboard_path)
        
        # Should have paused component
        assert "TestComponent" in dashboard.get("paused_components", {})
        
        # Should have action required alert
        assert "action_required_alerts" in dashboard
        if dashboard["action_required_alerts"]:
            alert = dashboard["action_required_alerts"][0]
            assert alert["error_type"] == "AUTHENTICATION"
            assert alert["component"] == "TestComponent"

    def test_transient_errors_still_respect_threshold(self, tmp_path):
        """Test transient errors still respect failure threshold after auth error handling."""
        logs_dir = tmp_path / "logs"
        dashboard_path = tmp_path / "dashboard.json"
        health_status_path = tmp_path / "health_status.json"

        error_logger = ErrorLogger(logs_dir, dashboard_path)

        cb = CircuitBreaker(
            component="TestComponent",
            failure_threshold=3,
            health_status_path=health_status_path,
            error_logger=error_logger
        )

        # Two transient errors should not open circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(lambda: (_ for _ in ()).throw(Exception("Transient failure")))
            assert cb.state == CircuitBreakerState.CLOSED

        # Third transient error should open circuit
        with pytest.raises(Exception):
            cb.call(lambda: (_ for _ in ()).throw(Exception("Transient failure")))
        assert cb.state == CircuitBreakerState.OPEN
