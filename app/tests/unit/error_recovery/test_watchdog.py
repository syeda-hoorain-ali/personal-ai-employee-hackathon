"""
Unit tests for Watchdog class.

Tests cover:
- T078: Test component registration and startup
- T079: Test crash detection and restart
- T080: Test crash loop detection (3 crashes in 5 minutes)
- T081: Test component pause after max restart attempts
"""

import pytest
import time
from pathlib import Path
from datetime import datetime, UTC, timedelta
import tempfile
import shutil
import os

from app.error_recovery.watchdog import Watchdog, ComponentConfig
from app.error_recovery.error_logger import ErrorLogger
from app.error_recovery.entities import ComponentStatus


@pytest.fixture
def temp_vault():
    """Create temporary vault directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    logs_dir = temp_dir / "Logs" / "Errors"
    system_dir = temp_dir / ".system"

    logs_dir.mkdir(parents=True)
    system_dir.mkdir(parents=True)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def error_logger(temp_vault):
    """Create ErrorLogger instance for testing."""
    logs_dir = temp_vault / "Logs" / "Errors"
    dashboard_path = temp_vault / ".system" / "error_dashboard.json"
    return ErrorLogger(logs_dir, dashboard_path)


@pytest.fixture
def watchdog(temp_vault, error_logger):
    """Create Watchdog instance for testing."""
    return Watchdog(
        vault_path=temp_vault,
        check_interval_seconds=1,  # Short interval for testing
        error_logger=error_logger
    )


# Mock component functions
class MockComponent:
    """Mock component for testing."""

    def __init__(self):
        self.start_count = 0
        self.is_healthy = True
        self.should_crash = False
        self.pid = None

    def start(self) -> int:
        """Mock start function that returns a PID."""
        self.start_count += 1
        if self.should_crash:
            return 0  # Simulate start failure
        self.pid = os.getpid() + self.start_count  # Fake PID
        return self.pid

    def health_check(self) -> bool:
        """Mock health check function."""
        return self.is_healthy


# T078: Test component registration and startup
def test_component_registration(watchdog):
    """Test that components can be registered with the watchdog."""
    mock_component = MockComponent()

    config = ComponentConfig(
        name="TestComponent",
        start_command=mock_component.start,
        health_check=mock_component.health_check,
        restart_on_failure=True,
        max_restart_attempts=3
    )

    # Register component
    watchdog.register_component(config)

    # Verify component is registered
    assert "TestComponent" in watchdog.components
    assert watchdog.components["TestComponent"] == config
    assert watchdog.restart_counts["TestComponent"] == 0
    assert watchdog.crash_history["TestComponent"] == []


def test_component_startup(watchdog):
    """Test that registered components are started."""
    mock_component = MockComponent()

    config = ComponentConfig(
        name="TestComponent",
        start_command=mock_component.start,
        health_check=mock_component.health_check
    )

    watchdog.register_component(config)

    # Start component
    success = watchdog._start_component("TestComponent")

    # Verify component started
    assert success is True
    assert mock_component.start_count == 1
    assert "TestComponent" in watchdog.component_pids
    assert watchdog.component_pids["TestComponent"] == mock_component.pid

    # Verify status is tracked
    status = watchdog.get_component_status("TestComponent")
    assert status is not None
    assert status.component == "TestComponent"
    assert status.status == ComponentStatus.STARTING
    assert status.process_id == mock_component.pid


def test_component_startup_failure(watchdog):
    """Test handling of component startup failure."""
    mock_component = MockComponent()
    mock_component.should_crash = True

    config = ComponentConfig(
        name="FailingComponent",
        start_command=mock_component.start
    )

    watchdog.register_component(config)

    # Try to start component
    success = watchdog._start_component("FailingComponent")

    # Verify startup failed
    assert success is False
    assert "FailingComponent" not in watchdog.component_pids


# T079: Test crash detection and restart
def test_crash_detection_and_restart(watchdog):
    """Test that crashed components are detected and restarted."""
    mock_component = MockComponent()

    config = ComponentConfig(
        name="TestComponent",
        start_command=mock_component.start,
        health_check=mock_component.health_check,
        restart_on_failure=True,
        max_restart_attempts=3,
        restart_backoff_seconds=0  # No backoff for testing
    )

    watchdog.register_component(config)
    watchdog._start_component("TestComponent")

    # Simulate component becoming unhealthy
    mock_component.is_healthy = False

    # Restart component
    success = watchdog.restart_component("TestComponent")

    # Verify restart occurred
    assert success is True
    assert mock_component.start_count == 2  # Started twice (initial + restart)
    assert watchdog.restart_counts["TestComponent"] == 1
    assert len(watchdog.crash_history["TestComponent"]) == 1


def test_restart_respects_max_attempts(watchdog):
    """Test that components are paused after max restart attempts."""
    mock_component = MockComponent()

    config = ComponentConfig(
        name="TestComponent",
        start_command=mock_component.start,
        restart_on_failure=True,
        max_restart_attempts=2,
        restart_backoff_seconds=0
    )

    watchdog.register_component(config)
    watchdog._start_component("TestComponent")

    # Restart multiple times
    watchdog.restart_component("TestComponent")  # Restart 1
    watchdog.restart_component("TestComponent")  # Restart 2

    # Third restart should fail and pause component
    success = watchdog.restart_component("TestComponent")

    # Verify component was paused
    assert success is False
    status = watchdog.get_component_status("TestComponent")
    assert status is not None
    assert status.status == ComponentStatus.PAUSED


def test_restart_disabled_component(watchdog):
    """Test that components with restart_on_failure=False are not restarted."""
    mock_component = MockComponent()

    config = ComponentConfig(
        name="NoRestartComponent",
        start_command=mock_component.start,
        restart_on_failure=False
    )

    watchdog.register_component(config)
    watchdog._start_component("NoRestartComponent")

    # Try to restart
    success = watchdog.restart_component("NoRestartComponent")

    # Verify restart was not attempted
    assert success is False
    assert mock_component.start_count == 1  # Only initial start


# T080: Test crash loop detection (3 crashes in 5 minutes)
def test_crash_loop_detection(watchdog):
    """Test that crash loops are detected (3 crashes in 5 minutes)."""
    mock_component = MockComponent()

    config = ComponentConfig(
        name="CrashLoopComponent",
        start_command=mock_component.start,
        restart_on_failure=True,
        max_restart_attempts=10,  # High limit to test crash loop detection
        restart_backoff_seconds=0,
        crash_detection_window_minutes=5,
        crash_threshold=3
    )

    watchdog.register_component(config)
    watchdog._start_component("CrashLoopComponent")

    # Simulate 3 crashes within the window
    now = datetime.now(UTC)
    watchdog.crash_history["CrashLoopComponent"] = [
        (now - timedelta(minutes=4)).isoformat().replace('+00:00', 'Z'),
        (now - timedelta(minutes=2)).isoformat().replace('+00:00', 'Z'),
        (now - timedelta(minutes=1)).isoformat().replace('+00:00', 'Z')
    ]

    # Check if crash loop is detected
    is_crash_loop = watchdog._is_crash_loop("CrashLoopComponent")
    assert is_crash_loop is True

    # Try to restart - should be paused due to crash loop
    success = watchdog.restart_component("CrashLoopComponent")

    # Verify component was paused
    assert success is False
    status = watchdog.get_component_status("CrashLoopComponent")
    assert status is not None
    assert status.status == ComponentStatus.PAUSED


def test_crash_loop_not_detected_outside_window(watchdog):
    """Test that old crashes outside the window don't trigger crash loop detection."""
    mock_component = MockComponent()

    config = ComponentConfig(
        name="TestComponent",
        start_command=mock_component.start,
        restart_on_failure=True,
        max_restart_attempts=10,
        restart_backoff_seconds=0,
        crash_detection_window_minutes=5,
        crash_threshold=3
    )

    watchdog.register_component(config)
    watchdog._start_component("TestComponent")

    # Simulate crashes outside the window
    now = datetime.now(UTC)
    watchdog.crash_history["TestComponent"] = [
        (now - timedelta(minutes=10)).isoformat().replace('+00:00', 'Z'),
        (now - timedelta(minutes=8)).isoformat().replace('+00:00', 'Z'),
        (now - timedelta(minutes=6)).isoformat().replace('+00:00', 'Z')
    ]

    # Check if crash loop is detected
    is_crash_loop = watchdog._is_crash_loop("TestComponent")
    assert is_crash_loop is False


def test_crash_loop_below_threshold(watchdog):
    """Test that crash loop is not detected below threshold."""
    mock_component = MockComponent()

    config = ComponentConfig(
        name="TestComponent",
        start_command=mock_component.start,
        restart_on_failure=True,
        crash_detection_window_minutes=5,
        crash_threshold=3
    )

    watchdog.register_component(config)

    # Simulate only 2 crashes (below threshold of 3)
    now = datetime.now(UTC)
    watchdog.crash_history["TestComponent"] = [
        (now - timedelta(minutes=2)).isoformat().replace('+00:00', 'Z'),
        (now - timedelta(minutes=1)).isoformat().replace('+00:00', 'Z')
    ]

    # Check if crash loop is detected
    is_crash_loop = watchdog._is_crash_loop("TestComponent")
    assert is_crash_loop is False


# T081: Test component pause after max restart attempts
def test_component_pause(watchdog):
    """Test that components can be paused."""
    mock_component = MockComponent()

    config = ComponentConfig(
        name="TestComponent",
        start_command=mock_component.start
    )

    watchdog.register_component(config)
    watchdog._start_component("TestComponent")

    # Pause component
    watchdog.pause_component("TestComponent", "Manual pause for testing")

    # Verify component is paused
    status = watchdog.get_component_status("TestComponent")
    assert status is not None
    assert status.status == ComponentStatus.PAUSED

    # Verify component is not in active PIDs
    assert "TestComponent" not in watchdog.component_pids


def test_paused_component_not_checked(watchdog):
    """Test that paused components are skipped during health checks."""
    mock_component = MockComponent()

    config = ComponentConfig(
        name="PausedComponent",
        start_command=mock_component.start,
        health_check=mock_component.health_check
    )

    watchdog.register_component(config)
    watchdog._start_component("PausedComponent")

    # Pause component
    watchdog.pause_component("PausedComponent", "Test pause")

    # Make component unhealthy
    mock_component.is_healthy = False

    # Run health check
    initial_restart_count = watchdog.restart_counts["PausedComponent"]
    watchdog._check_all_components()

    # Verify no restart was attempted (component is paused)
    assert watchdog.restart_counts["PausedComponent"] == initial_restart_count

    # Verify status is still paused
    status = watchdog.get_component_status("PausedComponent")
    assert status is not None
    assert status.status == ComponentStatus.PAUSED


def test_get_all_status(watchdog):
    """Test getting status of all components."""
    mock_component1 = MockComponent()
    mock_component2 = MockComponent()

    config1 = ComponentConfig(name="Component1", start_command=mock_component1.start)
    config2 = ComponentConfig(name="Component2", start_command=mock_component2.start)

    watchdog.register_component(config1)
    watchdog.register_component(config2)

    watchdog._start_component("Component1")
    watchdog._start_component("Component2")

    # Get all status
    all_status = watchdog.get_all_status()

    # Verify both components are in status
    assert len(all_status) == 2
    assert "Component1" in all_status
    assert "Component2" in all_status
    assert all_status["Component1"].component == "Component1"
    assert all_status["Component2"].component == "Component2"


def test_state_persistence(watchdog, temp_vault):
    """Test that watchdog state is persisted and loaded."""
    mock_component = MockComponent()

    config = ComponentConfig(
        name="TestComponent",
        start_command=mock_component.start
    )

    watchdog.register_component(config)
    watchdog._start_component("TestComponent")

    # Simulate some restarts and crashes
    watchdog.restart_counts["TestComponent"] = 2
    watchdog.crash_history["TestComponent"] = [
        datetime.now(UTC).isoformat().replace('+00:00', 'Z')
    ]

    # Save state
    watchdog._save_state()

    # Create new watchdog instance (should load state)
    new_watchdog = Watchdog(
        vault_path=temp_vault,
        check_interval_seconds=1
    )

    # Verify state was loaded
    assert new_watchdog.restart_counts.get("TestComponent") == 2
    assert len(new_watchdog.crash_history.get("TestComponent", [])) == 1
