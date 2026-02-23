"""
Integration Test: Concurrent Task Claiming (T056)

Tests that only one agent can claim a task when multiple agents attempt simultaneously.
This validates the atomic claim-by-move protocol using os.replace().

Run this test with: pytest tests/integration/test_concurrent_claiming.py -v
"""

import os
import time
import threading
from pathlib import Path
from datetime import datetime

import pytest

from src.app.claim_protocol.claim_manager import ClaimManager
from src.app.domain_manager.domain_config import DomainConfig


@pytest.fixture
def vault_path(tmp_path):
    """Create temporary vault structure for testing."""
    vault = tmp_path / "AI_Employee_Vault"

    # Create directory structure
    (vault / "Needs_Action" / "email").mkdir(parents=True)
    (vault / "In_Progress" / "cloud-agent").mkdir(parents=True)
    (vault / "In_Progress" / "local-agent").mkdir(parents=True)
    (vault / ".config").mkdir(parents=True)

    # Create domain config
    domain_config = """
domains:
  email:
    description: "Email triage and responses"
    allowed_agents: ["cloud-agent", "local-agent"]
  social:
    description: "Social media management"
    allowed_agents: ["cloud-agent", "local-agent"]
  local-only:
    description: "Local-exclusive tasks"
    allowed_agents: ["local-agent"]

agents:
  cloud-agent:
    allowed_domains: ["email", "social"]
  local-agent:
    allowed_domains: ["email", "social", "local-only"]
"""
    (vault / ".config" / "domains.yaml").write_text(domain_config)

    return vault


@pytest.fixture
def test_task(vault_path):
    """Create a test task file in Needs_Action/email/."""
    task_content = """---
id: task-test-001
domain: email
priority: high
created: 2026-02-23T10:00:00Z
claimed_by: null
claimed_at: null
status: pending
source: test
---

# Test Task

This is a test task for concurrent claiming validation.
"""
    task_path = vault_path / "Needs_Action" / "email" / "task-test-001.md"
    task_path.write_text(task_content)
    return task_path


def claim_task_worker(claim_manager, task_file, domain, agent_name, results, index):
    """Worker function to attempt claiming a task."""
    try:
        result = claim_manager.claim_task(task_file, domain)
        results[index] = {
            "agent": agent_name,
            "success": result.get("success", False),
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        results[index] = {
            "agent": agent_name,
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def test_concurrent_claim_single_winner(vault_path, test_task):
    """
    Test T056: Verify only one agent claims task when multiple attempt simultaneously.

    Expected behavior:
    - Only ONE agent successfully claims the task
    - Other agents receive False (task already claimed)
    - Task file moves to In_Progress/<winning-agent>/
    - No race conditions or duplicate claims
    """
    # Setup
    os.environ["VAULT_PATH"] = str(vault_path)

    claim_manager_1 = ClaimManager(str(vault_path), "cloud-agent")
    claim_manager_2 = ClaimManager(str(vault_path), "local-agent")

    task_file = test_task
    domain = "email"

    # Launch concurrent claim attempts
    results = [None, None]
    threads = [
        threading.Thread(
            target=claim_task_worker,
            args=(claim_manager_1, task_file, domain, "cloud-agent", results, 0)
        ),
        threading.Thread(
            target=claim_task_worker,
            args=(claim_manager_2, task_file, domain, "local-agent", results, 1)
        )
    ]

    # Start both threads simultaneously
    for thread in threads:
        thread.start()

    # Wait for completion
    for thread in threads:
        thread.join()

    # Validate results
    successful_claims = [r for r in results if r and r["success"]]
    failed_claims = [r for r in results if r and not r["success"]]

    # Assertions
    assert len(successful_claims) == 1, f"Expected exactly 1 successful claim, got {len(successful_claims)}"
    assert len(failed_claims) == 1, f"Expected exactly 1 failed claim, got {len(failed_claims)}"

    winner = successful_claims[0]["agent"]
    print(f"\n[PASS] Winner: {winner}")
    print(f"[PASS] Loser: {failed_claims[0]['agent']}")

    # Verify task moved to correct location
    task_filename = task_file.name
    expected_path = vault_path / "In_Progress" / winner / task_filename
    assert expected_path.exists(), f"Task should be in In_Progress/{winner}/"

    # Verify task NOT in original location
    assert not task_file.exists(), "Task should NOT remain in Needs_Action/"

    # Verify task NOT in loser's directory
    loser = failed_claims[0]["agent"]
    loser_path = vault_path / "In_Progress" / loser / task_filename
    assert not loser_path.exists(), f"Task should NOT be in In_Progress/{loser}/"

    print(f"[PASS] Task correctly moved to In_Progress/{winner}/")
    print("[PASS] No duplicate claims detected")
    print("[PASS] Atomic claim-by-move protocol validated")


def test_concurrent_claim_stress_test(vault_path):
    """
    Stress test: 10 agents attempting to claim 5 tasks simultaneously.

    Expected behavior:
    - Each task claimed by exactly one agent
    - No race conditions
    - No lost tasks
    """
    # Setup
    os.environ["VAULT_PATH"] = str(vault_path)

    # Create 5 test tasks
    num_tasks = 5
    task_files = []
    for i in range(num_tasks):
        task_content = f"""---
id: task-stress-{i:03d}
domain: email
priority: medium
created: 2026-02-23T10:00:00Z
claimed_by: null
claimed_at: null
status: pending
source: test
---

# Stress Test Task {i}
"""
        task_path = vault_path / "Needs_Action" / "email" / f"task-stress-{i:03d}.md"
        task_path.write_text(task_content)
        task_files.append(task_path)

    # Create 10 claim managers (simulating 10 agents)
    num_agents = 10
    claim_managers = []
    for i in range(num_agents):
        agent_name = f"agent-{i:02d}"
        # Create agent directory
        (vault_path / "In_Progress" / agent_name).mkdir(parents=True)
        claim_managers.append(
            ClaimManager(str(vault_path), agent_name)
        )

    # Launch concurrent claims
    results = {}
    threads = []
    domain = "email"

    for task_idx in range(num_tasks):
        task_file = task_files[task_idx]
        task_name = task_file.name
        results[task_name] = [None] * num_agents

        for agent_idx in range(num_agents):
            thread = threading.Thread(
                target=claim_task_worker,
                args=(
                    claim_managers[agent_idx],
                    task_file,
                    domain,
                    f"agent-{agent_idx:02d}",
                    results[task_name],
                    agent_idx
                )
            )
            threads.append(thread)

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for completion
    for thread in threads:
        thread.join()

    # Validate results
    for task_name, task_results in results.items():
        successful_claims = [r for r in task_results if r and r["success"]]

        assert len(successful_claims) == 1, (
            f"Task {task_name}: Expected exactly 1 claim, got {len(successful_claims)}"
        )

        winner = successful_claims[0]["agent"]
        print(f"[PASS] {task_name} claimed by {winner}")

    print(f"\n[PASS] All {num_tasks} tasks claimed by exactly one agent")
    print(f"[PASS] No race conditions in {num_agents * num_tasks} concurrent attempts")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
