"""
Unit tests for the Ralph Wiggum Controller functionality.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from app.ralph_wiggum_controller import RalphWiggumController


@pytest.fixture
def temp_vault():
    """Create a temporary vault directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_path = Path(temp_dir)

        # Create required directories
        (vault_path / "Plans").mkdir(exist_ok=True)
        (vault_path / "Done").mkdir(exist_ok=True)
        (vault_path / "Needs_Action").mkdir(exist_ok=True)

        yield vault_path


def test_ralph_wiggum_controller_initialization(temp_vault):
    """Test that the Ralph Wiggum controller initializes correctly."""
    controller = RalphWiggumController(str(temp_vault), max_iterations=5)

    assert controller.vault_path == temp_vault
    assert controller.max_iterations == 5
    assert controller.logger is not None


def test_create_plan_file(temp_vault):
    """Test that the controller can create a plan file."""
    controller = RalphWiggumController(str(temp_vault), max_iterations=5)

    task_desc = "Test task for creating a plan file"
    iteration = 1

    plan_file = controller._create_plan_file(task_desc, iteration)

    assert plan_file.exists()
    assert "Test task for creating a plan file" in plan_file.read_text()
    assert "Iteration 1" in plan_file.read_text()
    assert plan_file.parent.name == "Plans"


@patch('subprocess.run')
def test_run_claude_with_prompt_success(mock_subprocess_run, temp_vault):
    """Test that Claude runs successfully with a prompt."""
    # Mock successful subprocess result
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Success"
    mock_subprocess_run.return_value = mock_result

    controller = RalphWiggumController(str(temp_vault), max_iterations=5)

    prompt = "Test prompt for Claude"
    success = controller._run_claude_with_prompt(prompt)

    assert success is True
    mock_subprocess_run.assert_called_once()


@patch('subprocess.run')
def test_run_claude_with_prompt_failure(mock_subprocess_run, temp_vault):
    """Test that Claude handles failures correctly."""
    # Mock failed subprocess result
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "Error occurred"
    mock_subprocess_run.return_value = mock_result

    controller = RalphWiggumController(str(temp_vault), max_iterations=5)

    prompt = "Test prompt for Claude"
    success = controller._run_claude_with_prompt(prompt)

    assert success is False
    mock_subprocess_run.assert_called_once()


def test_check_completion_condition_not_complete(temp_vault):
    """Test that the completion check returns False when task is not complete."""
    # Create a file in Needs_Action to ensure there are tasks to process
    needs_action_dir = temp_vault / "Needs_Action"
    needs_action_dir.mkdir(exist_ok=True)
    test_file = needs_action_dir / "test_task.md"
    test_file.write_text("Test task content")

    controller = RalphWiggumController(str(temp_vault), max_iterations=5)

    task_desc = "Test task that is not complete"
    is_complete = controller._check_completion_condition(task_desc)

    assert is_complete is False


def test_create_task_processing_prompt(temp_vault):
    """Test that task processing prompts are created correctly."""
    controller = RalphWiggumController(str(temp_vault), max_iterations=5)

    task_desc = "Process some files"
    iteration = 1
    plan_file = temp_vault / "Plans" / "test_plan.md"
    plan_file.write_text("Test plan content")

    prompt = controller._create_task_processing_prompt(task_desc, iteration, plan_file)

    assert task_desc in prompt
    assert f"This is iteration {iteration} of maximum {controller.max_iterations}" in prompt
    assert str(plan_file.relative_to(temp_vault)) in prompt
    assert "autonomous reasoning mode" in prompt.lower()
    assert "Claude Reasoning Layer Workflow" in prompt


@patch.object(RalphWiggumController, '_run_claude_with_prompt')
@patch.object(RalphWiggumController, '_check_completion_condition')
def test_run_reasoning_loop_single_iteration(mock_check_complete,
                                           mock_run_claude,
                                           temp_vault):
    """Test the reasoning loop with a single iteration."""
    # Mock the completion check to return True immediately
    mock_check_complete.return_value = True
    mock_run_claude.return_value = True

    controller = RalphWiggumController(str(temp_vault), max_iterations=5)

    task_desc = "Test task with single iteration"
    success = controller.run_reasoning_loop(task_desc)

    assert success is True
    mock_run_claude.assert_called_once()
    mock_check_complete.assert_called_once()


@patch.object(RalphWiggumController, '_run_claude_with_prompt')
@patch.object(RalphWiggumController, '_check_completion_condition')
def test_run_reasoning_loop_max_iterations(mock_check_complete,
                                         mock_run_claude,
                                         temp_vault):
    """Test the reasoning loop reaching max iterations."""
    # Mock the completion check to always return False
    mock_check_complete.return_value = False
    mock_run_claude.return_value = True

    controller = RalphWiggumController(str(temp_vault), max_iterations=3)

    task_desc = "Test task that reaches max iterations"
    success = controller.run_reasoning_loop(task_desc)

    assert success is False
    assert mock_run_claude.call_count == 3  # Called for each iteration
    assert mock_check_complete.call_count == 3  # Called for each iteration
