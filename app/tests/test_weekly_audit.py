"""
Comprehensive test suite for Weekly CEO Briefing feature.
Run with: python test_weekly_audit.py
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[attr-defined]

import tempfile
import csv
from pathlib import Path
from datetime import date, datetime, timedelta
from decimal import Decimal
import shutil

def test_module_imports():
    """Test that all modules can be imported."""
    print('Test 1: Module Imports')
    try:
        from src.app.weekly_audit import entities
        from src.app.weekly_audit import audit_orchestrator
        from src.app.weekly_audit import business_goals_parser
        from src.app.weekly_audit import task_analyzer
        from src.app.weekly_audit import transaction_analyzer
        from src.app.weekly_audit import subscription_detector
        from src.app.weekly_audit import briefing_generator
        from src.app.weekly_audit.schedulers import base_scheduler
        from src.app.weekly_audit.schedulers import windows_scheduler
        from src.app.weekly_audit.schedulers import unix_scheduler
        print('[PASS] All modules imported successfully\n')
        return True
    except Exception as e:
        print(f'[FAIL] Module import failed: {e}\n')
        return False

def test_entities():
    """Test entity creation and validation."""
    print('Test 2: Entity Creation')
    try:
        from src.app.weekly_audit.entities import (
            BusinessGoals, CompletedTask, Transaction,
            Subscription, TaskBottleneck, TransactionSummary
        )

        goals = BusinessGoals(
            revenue_target=Decimal('10000.00'),
            current_revenue=Decimal('3500.00'),
            key_metrics=[{'name': 'Test', 'target': '100%', 'alert_threshold': '80%'}],
            active_projects=[{'name': 'Project A', 'deadline': '2026-03-31', 'budget': 5000}],
            subscription_rules={'inactivity_days': 30, 'cost_increase_threshold': 0.20},
            last_updated=date(2026, 2, 19),
            review_frequency='weekly'
        )
        assert goals.revenue_target == Decimal('10000.00')
        print(f'  [PASS] BusinessGoals: revenue_target={goals.revenue_target}')

        task = CompletedTask(
            name='Test Task',
            completion_date=datetime.now(),
            expected_duration=timedelta(hours=2),
            actual_duration=timedelta(hours=3),
            priority='high',
            project='Test Project',
            file_path=Path('test_task.md')
        )
        assert task.name == 'Test Task'
        print(f'  [PASS] CompletedTask: {task.name}')

        transaction = Transaction(
            date=date(2026, 2, 15),
            amount=Decimal('-49.99'),
            description='Netflix Subscription',
            category='Entertainment',
            source_file=Path('transactions.csv')
        )
        assert transaction.amount == Decimal('-49.99')
        print(f'  [PASS] Transaction: {transaction.description}')

        print('[PASS] All entities created successfully\n')
        return True
    except Exception as e:
        print(f'[FAIL] Entity creation failed: {e}\n')
        return False

def test_business_goals_parser():
    """Test BusinessGoalsParser with sample data."""
    print('Test 3: BusinessGoalsParser')
    try:
        from src.app.weekly_audit.business_goals_parser import BusinessGoalsParser

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""---
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
Test content
""")
            goals_file = Path(f.name)

        parser = BusinessGoalsParser(goals_file)
        goals = parser.parse()
        goals_file.unlink()

        assert goals.revenue_target == Decimal('10000.00'), 'Revenue target mismatch'
        assert goals.current_revenue == Decimal('3500.00'), 'Current revenue mismatch'
        assert len(goals.key_metrics) == 1, 'Key metrics count mismatch'
        assert len(goals.active_projects) == 1, 'Active projects count mismatch'

        print(f'  [PASS] Parsed revenue_target: {goals.revenue_target}')
        print(f'  [PASS] Parsed {len(goals.key_metrics)} metrics, {len(goals.active_projects)} projects')
        print('[PASS] BusinessGoalsParser test passed\n')
        return True
    except Exception as e:
        print(f'[FAIL] BusinessGoalsParser test failed: {e}\n')
        return False

def test_transaction_analyzer():
    """Test TransactionAnalyzer with sample CSV data."""
    print('Test 4: TransactionAnalyzer')
    try:
        from src.app.weekly_audit.transaction_analyzer import TransactionAnalyzer

        temp_dir = Path(tempfile.mkdtemp())
        csv_file = temp_dir / 'transactions.csv'

        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['date', 'amount', 'description', 'category'])
            writer.writerow(['2026-02-15', '2500.00', 'Client payment', 'Revenue'])
            writer.writerow(['2026-02-18', '1000.00', 'Consulting fee', 'Revenue'])
            writer.writerow(['2026-02-10', '-49.99', 'Netflix subscription', 'Entertainment'])
            writer.writerow(['2026-02-12', '-29.99', 'Spotify Premium', 'Entertainment'])
            writer.writerow(['2026-02-14', '-19.99', 'GitHub Pro', 'Software'])

        analyzer = TransactionAnalyzer(temp_dir)
        start_date = date(2026, 2, 1)
        end_date = date(2026, 2, 28)

        # Parse transactions first
        transactions = analyzer.parse_csv(start_date, end_date)

        # Then calculate summary
        summary = analyzer.calculate_summary(transactions, start_date, end_date)

        assert summary.total_revenue == Decimal('3500.00'), f'Revenue: {summary.total_revenue}'
        assert summary.total_expenses == Decimal('99.97'), f'Expenses: {summary.total_expenses}'
        assert summary.net_income == Decimal('3400.03'), f'Net: {summary.net_income}'
        assert summary.transaction_count == 5, f'Count: {summary.transaction_count}'

        print(f'  [PASS] Revenue: ${summary.total_revenue}')
        print(f'  [PASS] Expenses: ${summary.total_expenses}')
        print(f'  [PASS] Net Income: ${summary.net_income}')
        print(f'  [PASS] Transaction Count: {summary.transaction_count}')

        shutil.rmtree(temp_dir)
        print('[PASS] TransactionAnalyzer test passed\n')
        return True
    except Exception as e:
        print(f'[FAIL] TransactionAnalyzer test failed: {e}\n')
        return False

def test_subscription_detector():
    """Test SubscriptionDetector with sample transactions."""
    print('Test 5: SubscriptionDetector')
    try:
        from src.app.weekly_audit.transaction_analyzer import TransactionAnalyzer
        from src.app.weekly_audit.subscription_detector import SubscriptionDetector

        temp_dir = Path(tempfile.mkdtemp())
        csv_file = temp_dir / 'transactions.csv'

        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['date', 'amount', 'description', 'category'])
            writer.writerow(['2026-02-10', '-49.99', 'Netflix subscription', 'Entertainment'])
            writer.writerow(['2026-01-10', '-49.99', 'Netflix subscription', 'Entertainment'])
            writer.writerow(['2025-12-10', '-49.99', 'Netflix subscription', 'Entertainment'])

        analyzer = TransactionAnalyzer(temp_dir)
        start_date = date(2025, 12, 1)
        end_date = date(2026, 2, 28)
        transactions = analyzer.parse_csv(start_date, end_date)

        detector = SubscriptionDetector()
        subscriptions = detector.detect_subscriptions(transactions)
        flagged_subscriptions = detector.flag_subscriptions(subscriptions, no_activity_days=30, cost_increase_threshold=0.20)

        print(f'  [PASS] Detected {len(subscriptions)} subscriptions')
        for sub in subscriptions:
            print(f'    - {sub.name}: ${sub.amount} ({sub.frequency})')

        shutil.rmtree(temp_dir)
        print('[PASS] SubscriptionDetector test passed\n')
        return True
    except Exception as e:
        print(f'[FAIL] SubscriptionDetector test failed: {e}\n')
        return False

def test_task_analyzer():
    """Test TaskAnalyzer with sample task files."""
    print('Test 6: TaskAnalyzer')
    try:
        from src.app.weekly_audit.task_analyzer import TaskAnalyzer

        temp_dir = Path(tempfile.mkdtemp())
        done_dir = temp_dir / 'Done'
        done_dir.mkdir()

        task1 = done_dir / 'task1.md'
        task1.write_text("""---
expected_duration: 2h
actual_duration: 3.5h
priority: high
project: Test Project
---

# Task 1
Completed task with metadata
""", encoding='utf-8')

        task2 = done_dir / 'task2.md'
        task2.write_text('# Task 2\nSimple task without metadata', encoding='utf-8')

        analyzer = TaskAnalyzer(done_dir)
        tasks = analyzer.analyze_completed_tasks(days=7)

        assert len(tasks) == 2, f'Expected 2 tasks, got {len(tasks)}'
        print(f'  [PASS] Found {len(tasks)} completed tasks')

        bottlenecks = analyzer.identify_bottlenecks(tasks)
        print(f'  [PASS] Identified {len(bottlenecks)} bottlenecks')
        for bn in bottlenecks:
            print(f'    - {bn.task_name}: {bn.delay_percent}% delay')

        shutil.rmtree(temp_dir)
        print('[PASS] TaskAnalyzer test passed\n')
        return True
    except Exception as e:
        print(f'[FAIL] TaskAnalyzer test failed: {e}\n')
        return False

def main():
    """Run all tests and report results."""
    print('=' * 60)
    print('Weekly CEO Briefing - Test Suite')
    print('=' * 60)
    print()

    results = []
    results.append(('Module Imports', test_module_imports()))
    results.append(('Entity Creation', test_entities()))
    results.append(('BusinessGoalsParser', test_business_goals_parser()))
    results.append(('TransactionAnalyzer', test_transaction_analyzer()))
    results.append(('SubscriptionDetector', test_subscription_detector()))
    results.append(('TaskAnalyzer', test_task_analyzer()))

    print('=' * 60)
    print('Test Summary')
    print('=' * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = '[PASS]' if result else '[FAIL]'
        print(f'{status} {name}')

    print()
    print(f'Results: {passed}/{total} tests passed')

    if passed == total:
        print('\n✓ All tests passed successfully!')
        return 0
    else:
        print(f'\n✗ {total - passed} test(s) failed')
        return 1

if __name__ == '__main__':
    sys.exit(main())
