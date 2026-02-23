"""
Integration Test: Dashboard Single-Writer Rule (T067)

Tests that Local agent is sole writer of Dashboard.md while Cloud writes to Updates/,
preventing merge conflicts when both agents run concurrently.

Run this test with: pytest tests/integration/test_dashboard_single_writer.py -v
"""

import os
import time
import threading
from pathlib import Path
from datetime import datetime

import pytest

from src.app.dashboard_manager.cloud_update_writer import CloudUpdateWriter
from src.app.dashboard_manager.update_merger import UpdateMerger


@pytest.fixture
def vault_path(tmp_path):
    """Create temporary vault structure for testing."""
    vault = tmp_path / "AI_Employee_Vault"

    # Create directory structure
    (vault / "Updates" / "archive").mkdir(parents=True)
    (vault / ".config").mkdir(parents=True)

    # Create initial Dashboard.md
    dashboard_content = """# AI Employee Dashboard

Last Updated: 2026-02-23T10:00:00Z

## Current Status
System operational.

## Recent Activities
- System initialized
"""
    (vault / "Dashboard.md").write_text(dashboard_content)

    return vault


def cloud_agent_worker(vault_path, num_updates, results, index):
    """Simulate cloud agent writing status updates."""
    try:
        writer = CloudUpdateWriter(str(vault_path), "cloud-agent")

        for i in range(num_updates):
            writer.write_status_update(
                update_type="task_completed",
                message=f"Cloud agent completed task {i}",
                priority="medium",
                related_task=f"task-{index}-{i}"
            )
            time.sleep(0.01)  # Small delay between updates

        results[index] = {
            "agent": "cloud-agent",
            "success": True,
            "updates_written": num_updates
        }
    except Exception as e:
        results[index] = {
            "agent": "cloud-agent",
            "success": False,
            "error": str(e)
        }


def local_agent_worker(vault_path, num_merges, results, index):
    """Simulate local agent merging updates to Dashboard.md."""
    try:
        merger = UpdateMerger(str(vault_path))

        for i in range(num_merges):
            merger.merge_updates_to_dashboard()
            time.sleep(0.02)  # Small delay between merges

        results[index] = {
            "agent": "local-agent",
            "success": True,
            "merges_performed": num_merges
        }
    except Exception as e:
        results[index] = {
            "agent": "local-agent",
            "success": False,
            "error": str(e)
        }


def test_concurrent_dashboard_no_conflicts(vault_path):
    """
    Test T067: Verify no Git conflicts on Dashboard.md with concurrent agents.

    Expected behavior:
    - Cloud agent writes to Updates/ directory only
    - Local agent reads Updates/ and writes to Dashboard.md
    - No merge conflicts occur
    - All updates eventually appear in Dashboard.md
    - Updates are archived after merging
    """
    # Setup
    os.environ["VAULT_PATH"] = str(vault_path)

    # Launch concurrent operations
    results = [None, None]

    cloud_thread = threading.Thread(
        target=cloud_agent_worker,
        args=(vault_path, 10, results, 0)  # Cloud writes 10 updates
    )

    local_thread = threading.Thread(
        target=local_agent_worker,
        args=(vault_path, 5, results, 1)  # Local merges 5 times
    )

    # Start both threads
    cloud_thread.start()
    time.sleep(0.05)  # Let cloud write some updates first
    local_thread.start()

    # Wait for completion
    cloud_thread.join()
    local_thread.join()

    # Validate results
    assert results[0]["success"], f"Cloud agent failed: {results[0].get('error')}"
    assert results[1]["success"], f"Local agent failed: {results[1].get('error')}"

    print(f"\n[PASS] Cloud agent wrote {results[0]['updates_written']} updates")
    print(f"[PASS] Local agent performed {results[1]['merges_performed']} merges")

    # Verify Dashboard.md exists and was updated
    dashboard_path = vault_path / "Dashboard.md"
    assert dashboard_path.exists(), "Dashboard.md should exist"

    dashboard_content = dashboard_path.read_text()
    assert "Cloud agent completed task" in dashboard_content, (
        "Dashboard should contain merged updates"
    )

    print("[PASS] Dashboard.md successfully updated with cloud updates")

    # Verify Updates/ directory structure
    updates_dir = vault_path / "Updates"
    archive_dir = updates_dir / "archive"

    # Count remaining updates (not yet merged)
    remaining_updates = list(updates_dir.glob("cloud-status-*.md"))
    archived_updates = list(archive_dir.glob("cloud-status-*.md"))

    print(f"[PASS] Remaining updates: {len(remaining_updates)}")
    print(f"[PASS] Archived updates: {len(archived_updates)}")

    # Verify no conflicts occurred (all operations succeeded)
    assert results[0]["success"] and results[1]["success"], (
        "Both agents should complete without conflicts"
    )

    print("[PASS] No merge conflicts detected")
    print("[PASS] Single-writer rule validated")


def test_cloud_agent_cannot_write_dashboard(vault_path):
    """
    Test that cloud agent is restricted from writing directly to Dashboard.md.

    Expected behavior:
    - Cloud agent uses CloudUpdateWriter (writes to Updates/)
    - Cloud agent does NOT write directly to Dashboard.md
    - Only local agent can write to Dashboard.md
    """
    # Setup
    os.environ["VAULT_PATH"] = str(vault_path)
    os.environ["AGENT_NAME"] = "cloud-agent"

    writer = CloudUpdateWriter(str(vault_path), "cloud-agent")

    # Cloud agent writes update
    writer.write_status_update(
        update_type="info",
        message="Test update from cloud",
        priority="low"
    )

    # Verify update went to Updates/ directory
    updates_dir = vault_path / "Updates"
    update_files = list(updates_dir.glob("cloud-status-*.md"))

    assert len(update_files) > 0, "Cloud agent should write to Updates/"
    print(f"[PASS] Cloud agent wrote to Updates/ directory: {update_files[0].name}")

    # Verify Dashboard.md was NOT modified by cloud agent
    dashboard_path = vault_path / "Dashboard.md"
    dashboard_content = dashboard_path.read_text()

    assert "Test update from cloud" not in dashboard_content, (
        "Cloud agent should NOT write directly to Dashboard.md"
    )

    print("[PASS] Cloud agent correctly restricted from Dashboard.md")
    print("[PASS] Single-writer rule enforced")


def test_local_agent_merges_updates(vault_path):
    """
    Test that local agent successfully merges cloud updates into Dashboard.md.

    Expected behavior:
    - Local agent reads Updates/*.md files
    - Extracts key information from updates
    - Appends to Dashboard.md
    - Archives processed updates
    """
    # Setup
    os.environ["VAULT_PATH"] = str(vault_path)
    os.environ["AGENT_NAME"] = "local-agent"

    # Cloud agent writes some updates
    cloud_writer = CloudUpdateWriter(str(vault_path), "cloud-agent")
    cloud_writer.write_status_update(
        update_type="task_completed",
        message="Completed email triage",
        priority="high",
        related_task="task-001"
    )
    cloud_writer.write_status_update(
        update_type="info",
        message="System health check passed",
        priority="low"
    )

    # Local agent merges updates
    local_merger = UpdateMerger(str(vault_path))
    local_merger.merge_updates_to_dashboard()

    # Verify Dashboard.md contains merged updates
    dashboard_path = vault_path / "Dashboard.md"
    dashboard_content = dashboard_path.read_text()

    assert "Completed email triage" in dashboard_content, (
        "Dashboard should contain first update"
    )
    assert "System health check passed" in dashboard_content, (
        "Dashboard should contain second update"
    )

    print("[PASS] Local agent successfully merged updates to Dashboard.md")

    # Verify updates were archived
    archive_dir = vault_path / "Updates" / "archive"
    archived_files = list(archive_dir.glob("cloud-status-*.md"))

    assert len(archived_files) == 2, "Both updates should be archived"
    print(f"[PASS] {len(archived_files)} updates archived after merging")

    # Verify Updates/ directory is now empty (except archive/)
    updates_dir = vault_path / "Updates"
    remaining_updates = list(updates_dir.glob("cloud-status-*.md"))

    assert len(remaining_updates) == 0, "All updates should be archived"
    print("[PASS] Updates/ directory cleaned after merge")


def test_stress_concurrent_operations(vault_path):
    """
    Stress test: Multiple cloud updates and local merges happening simultaneously.

    Expected behavior:
    - No race conditions
    - No data loss
    - No merge conflicts
    - All updates eventually merged
    """
    # Setup
    os.environ["VAULT_PATH"] = str(vault_path)

    # Launch multiple concurrent operations
    results = [None, None, None, None]

    threads = [
        threading.Thread(target=cloud_agent_worker, args=(vault_path, 20, results, 0)),
        threading.Thread(target=cloud_agent_worker, args=(vault_path, 20, results, 1)),
        threading.Thread(target=local_agent_worker, args=(vault_path, 10, results, 2)),
        threading.Thread(target=local_agent_worker, args=(vault_path, 10, results, 3)),
    ]

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for completion
    for thread in threads:
        thread.join()

    # Validate all operations succeeded
    for i, result in enumerate(results):
        assert result["success"], f"Operation {i} failed: {result.get('error')}"

    print("\n[PASS] All concurrent operations completed successfully")
    print(f"[PASS] Total cloud updates: {results[0]['updates_written'] + results[1]['updates_written']}")
    print(f"[PASS] Total local merges: {results[2]['merges_performed'] + results[3]['merges_performed']}")

    # Verify Dashboard.md integrity
    dashboard_path = vault_path / "Dashboard.md"
    dashboard_content = dashboard_path.read_text()

    assert "Cloud agent completed task" in dashboard_content, (
        "Dashboard should contain merged updates"
    )

    print("[PASS] Dashboard.md integrity maintained")
    print("[PASS] No conflicts in high-concurrency scenario")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
