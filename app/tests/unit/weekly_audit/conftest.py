"""
Test fixtures for weekly audit unit tests.

This module provides reusable test data and mock objects for testing
the weekly audit components.
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock


@pytest.fixture
def mock_vault_path(tmp_path):
    """
    Create a temporary vault directory structure for testing.

    Returns:
        Path to the temporary vault directory
    """
    vault = tmp_path / "AI_Employee_Vault"
    vault.mkdir()

    # Create subdirectories
    (vault / "Done").mkdir()
    (vault / "Accounting").mkdir()
    (vault / "Briefings").mkdir()

    return vault


@pytest.fixture
def sample_business_goals():
    """
    Sample business goals data for testing.

    Returns:
        Dictionary with business goals data
    """
    return {
        "revenue_target": Decimal("10000.00"),
        "current_revenue": Decimal("3500.00"),
        "key_metrics": [
            {
                "name": "Client response time",
                "target": "< 24 hours",
                "alert_threshold": "> 48 hours"
            },
            {
                "name": "Invoice payment rate",
                "target": "> 90%",
                "alert_threshold": "< 80%"
            }
        ],
        "active_projects": [
            {
                "name": "Personal AI Employee",
                "deadline": "2026-02-28",
                "budget": 0
            }
        ],
        "subscription_rules": {
            "inactivity_days": 30,
            "cost_increase_threshold": 0.20
        },
        "last_updated": date(2026, 2, 19),
        "review_frequency": "weekly"
    }


@pytest.fixture
def sample_completed_tasks():
    """
    Sample completed tasks for testing.

    Returns:
        List of completed task dictionaries
    """
    return [
        {
            "name": "Create client proposal",
            "completion_date": datetime(2026, 2, 15, 14, 30),
            "expected_duration": timedelta(hours=2),
            "actual_duration": timedelta(hours=3, minutes=30),
            "priority": "high",
            "project": "client-alpha"
        },
        {
            "name": "Invoice processing",
            "completion_date": datetime(2026, 2, 14, 10, 0),
            "priority": "medium",
            "project": None
        },
        {
            "name": "Update documentation",
            "completion_date": datetime(2026, 2, 13, 16, 45),
            "expected_duration": timedelta(hours=1),
            "actual_duration": timedelta(minutes=45),
            "priority": "low",
            "project": "internal"
        }
    ]


@pytest.fixture
def sample_transactions():
    """
    Sample transactions for testing.

    Returns:
        List of transaction dictionaries
    """
    return [
        {
            "date": date(2026, 2, 15),
            "amount": Decimal("2500.00"),
            "description": "Client payment - Project Alpha",
            "category": "Revenue"
        },
        {
            "date": date(2026, 2, 14),
            "amount": Decimal("-49.99"),
            "description": "Netflix Subscription",
            "category": "Entertainment"
        },
        {
            "date": date(2026, 2, 13),
            "amount": Decimal("-29.99"),
            "description": "GitHub Pro Subscription",
            "category": "Software"
        },
        {
            "date": date(2026, 2, 12),
            "amount": Decimal("1000.00"),
            "description": "Consulting services",
            "category": "Revenue"
        },
        {
            "date": date(2026, 2, 11),
            "amount": Decimal("-15.99"),
            "description": "Spotify Premium",
            "category": "Entertainment"
        }
    ]


@pytest.fixture
def sample_subscriptions():
    """
    Sample detected subscriptions for testing.

    Returns:
        List of subscription dictionaries
    """
    return [
        {
            "name": "Netflix",
            "amount": Decimal("49.99"),
            "last_seen_date": date(2026, 2, 15),
            "frequency": "monthly",
            "pattern_matched": "netflix",
            "transaction_count": 3,
            "flags": ["No activity in 45 days"]
        },
        {
            "name": "GitHub Pro",
            "amount": Decimal("29.99"),
            "last_seen_date": date(2026, 2, 13),
            "frequency": "monthly",
            "pattern_matched": "github",
            "transaction_count": 2,
            "flags": []
        }
    ]


@pytest.fixture
def sample_bottlenecks():
    """
    Sample task bottlenecks for testing.

    Returns:
        List of bottleneck dictionaries
    """
    return [
        {
            "task_name": "Create client proposal",
            "expected_duration": timedelta(hours=2),
            "actual_duration": timedelta(hours=3, minutes=30),
            "delay_percent": 75.0,
            "completion_date": date(2026, 2, 15)
        }
    ]


@pytest.fixture
def sample_transaction_summary():
    """
    Sample transaction summary for testing.

    Returns:
        Dictionary with transaction summary data
    """
    return {
        "total_revenue": Decimal("3500.00"),
        "total_expenses": Decimal("1250.50"),
        "net_income": Decimal("2249.50"),
        "transaction_count": 47,
        "subscription_count": 8,
        "top_expense_categories": [
            {"category": "Software", "amount": Decimal("450.00")},
            {"category": "Entertainment", "amount": Decimal("150.00")},
            {"category": "Office Supplies", "amount": Decimal("85.50")}
        ],
        "period_start": date(2026, 2, 10),
        "period_end": date(2026, 2, 16)
    }


@pytest.fixture
def sample_business_goals_yaml():
    """
    Sample Business_Goals.md YAML frontmatter for testing.

    Returns:
        String with YAML frontmatter
    """
    return """---
revenue_target: 10000.00
current_revenue: 3500.00
key_metrics:
  - name: "Client response time"
    target: "< 24 hours"
    alert_threshold: "> 48 hours"
  - name: "Invoice payment rate"
    target: "> 90%"
    alert_threshold: "< 80%"
active_projects:
  - name: "Personal AI Employee"
    deadline: "2026-02-28"
    budget: 0
subscription_rules:
  inactivity_days: 30
  cost_increase_threshold: 0.20
last_updated: "2026-02-19"
review_frequency: "weekly"
---

# Business Goals

This file contains business goals and metrics.
"""


@pytest.fixture
def sample_csv_content():
    """
    Sample CSV transaction data for testing.

    Returns:
        String with CSV content
    """
    return """date,amount,description,category
2026-02-15,2500.00,Client payment - Project Alpha,Revenue
2026-02-14,-49.99,Netflix Subscription,Entertainment
2026-02-13,-29.99,GitHub Pro Subscription,Software
2026-02-12,1000.00,Consulting services,Revenue
2026-02-11,-15.99,Spotify Premium,Entertainment
"""
