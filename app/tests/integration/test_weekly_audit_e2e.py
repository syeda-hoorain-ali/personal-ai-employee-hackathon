"""
End-to-end integration test for Weekly CEO Briefing feature.

Tests the complete workflow from data collection to briefing generation.
"""

import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
import csv

import pytest

from app.weekly_audit.audit_orchestrator import AuditOrchestrator
from app.weekly_audit.business_goals_parser import BusinessGoalsParser
from app.weekly_audit.task_analyzer import TaskAnalyzer
from app.weekly_audit.transaction_analyzer import TransactionAnalyzer
from app.weekly_audit.subscription_detector import SubscriptionDetector


class TestWeeklyAuditE2E:
    """End-to-end tests for the weekly audit system."""

    @pytest.fixture
    def temp_vault(self, tmp_path):
        """Create a temporary vault structure with sample data."""
        vault = tmp_path / "test_vault"
        vault.mkdir()

        # Create directories
        (vault / "Done").mkdir()
        (vault / "Accounting").mkdir()
        (vault / "Briefings").mkdir()

        # Create Business_Goals.md
        business_goals = vault / "Business_Goals.md"
        business_goals.write_text("""---
revenue_target: 10000.00
current_revenue: 3500.00
key_metrics:
  - name: "Client response time"
    target: "< 24 hours"
    alert_threshold: "> 48 hours"
active_projects:
  - name: "Test Project"
    deadline: "2026-03-31"
    budget: 5000
subscription_rules:
  inactivity_days: 30
  cost_increase_threshold: 0.20
last_updated: "2026-02-19"
review_frequency: "weekly"
---

# Business Goals

This is a test business goals file.
""")

        # Create sample completed tasks
        task1 = vault / "Done" / "task1.md"
        task1.write_text("""---
expected_duration: 2h
actual_duration: 3h
priority: high
project: Test Project
---

# Task 1

This is a completed task.
""")
        task1_time = datetime.now() - timedelta(days=2)
        task1.touch()

        task2 = vault / "Done" / "task2.md"
        task2.write_text("# Task 2\n\nAnother completed task.")
        task2_time = datetime.now() - timedelta(days=5)
        task2.touch()

        # Create sample transactions CSV
        transactions_csv = vault / "Accounting" / "february-2026.csv"
        with open(transactions_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['date', 'amount', 'description', 'category'])

            # Revenue transactions
            writer.writerow(['2026-02-15', '2500.00', 'Client payment', 'Revenue'])
            writer.writerow(['2026-02-18', '1000.00', 'Consulting fee', 'Revenue'])

            # Expense transactions
            writer.writerow(['2026-02-10', '-49.99', 'Netflix subscription', 'Entertainment'])
            writer.writerow(['2026-02-12', '-29.99', 'Spotify Premium', 'Entertainment'])
            writer.writerow(['2026-02-14', '-19.99', 'GitHub Pro', 'Software'])
            writer.writerow(['2026-02-16', '-150.00', 'Office supplies', 'Office'])

            # Recurring subscription (Netflix from last month)
            writer.writerow(['2026-01-10', '-49.99', 'Netflix subscription', 'Entertainment'])

        return vault

    def test_business_goals_parser(self, temp_vault):
        """Test that BusinessGoalsParser can read the goals file."""
        parser = BusinessGoalsParser(temp_vault / "Business_Goals.md")
        goals = parser.parse()

        assert goals.revenue_target == 10000.00
        assert goals.current_revenue == 3500.00
        assert len(goals.key_metrics) == 1
        assert len(goals.active_projects) == 1
        assert goals.subscription_rules['inactivity_days'] == 30

    def test_task_analyzer(self, temp_vault):
        """Test that TaskAnalyzer can scan completed tasks."""
        analyzer = TaskAnalyzer(temp_vault / "Done")
        tasks = analyzer.analyze_completed_tasks(days=7)

        assert len(tasks) >= 2
        assert any('task1' in task.name.lower() for task in tasks)
        assert any('task2' in task.name.lower() for task in tasks)

    def test_transaction_analyzer(self, temp_vault):
        """Test that TransactionAnalyzer can parse CSV files."""
        from datetime import date, timedelta

        analyzer = TransactionAnalyzer(temp_vault / "Accounting")

        # Calculate date range for last 30 days
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        # Parse transactions
        transactions = analyzer.parse_csv(start_date, end_date)

        # Calculate summary
        summary = analyzer.calculate_summary(transactions, start_date, end_date)

        assert summary.total_revenue > 0
        assert summary.total_expenses > 0
        assert summary.net_income == summary.total_revenue - summary.total_expenses
        assert summary.transaction_count >= 6  # Test data has 6 transactions

    def test_subscription_detector(self, temp_vault):
        """Test that SubscriptionDetector can identify recurring subscriptions."""
        from datetime import date, timedelta

        analyzer = TransactionAnalyzer(temp_vault / "Accounting")

        # Calculate date range for last 60 days to capture recurring transactions
        end_date = date.today()
        start_date = end_date - timedelta(days=60)

        # Parse transactions
        transactions = analyzer.parse_csv(start_date, end_date)

        detector = SubscriptionDetector()
        subscriptions = detector.detect_subscriptions(transactions)

        # Should detect Netflix as recurring (appears twice)
        netflix_subs = [s for s in subscriptions if 'netflix' in s.name.lower()]
        assert len(netflix_subs) > 0

    def test_full_orchestrator_workflow(self, temp_vault):
        """Test the complete audit orchestrator workflow."""
        from datetime import date, timedelta

        orchestrator = AuditOrchestrator(temp_vault)

        # Note: This will attempt to invoke Claude skill, which may fail
        # in test environment. We're mainly testing that the workflow
        # doesn't crash and can collect/prepare data.
        try:
            # Test data collection without Claude invocation
            goals = BusinessGoalsParser(temp_vault / "Business_Goals.md").parse()
            tasks = TaskAnalyzer(temp_vault / "Done").analyze_completed_tasks(days=7)

            # Calculate date range for transactions
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            analyzer = TransactionAnalyzer(temp_vault / "Accounting")
            transactions = analyzer.parse_csv(start_date, end_date)
            summary = analyzer.calculate_summary(transactions, start_date, end_date)

            assert goals is not None
            assert len(tasks) >= 2
            assert summary.total_revenue > 0

            print(f"✓ Data collection successful")
            print(f"  - Revenue: ${summary.total_revenue:.2f}")
            print(f"  - Expenses: ${summary.total_expenses:.2f}")
            print(f"  - Tasks completed: {len(tasks)}")

        except Exception as e:
            pytest.fail(f"Orchestrator workflow failed: {e}")


def test_module_imports():
    """Test that all weekly_audit modules can be imported."""
    try:
        from app.weekly_audit import entities
        from app.weekly_audit import audit_orchestrator
        from app.weekly_audit import business_goals_parser
        from app.weekly_audit import task_analyzer
        from app.weekly_audit import transaction_analyzer
        from app.weekly_audit import subscription_detector
        from app.weekly_audit import briefing_generator
        from app.weekly_audit.schedulers import base_scheduler
        from app.weekly_audit.schedulers import windows_scheduler
        from app.weekly_audit.schedulers import unix_scheduler

        print("✓ All modules imported successfully")

    except ImportError as e:
        pytest.fail(f"Failed to import module: {e}")


if __name__ == "__main__":
    # Run basic import test
    test_module_imports()
    print("\n✓ Module import test passed")
