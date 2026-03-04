"""
Orchestrator for the weekly business audit process.

This module coordinates the entire audit workflow: data collection, analysis,
context preparation, Claude skill invocation, and output verification.
"""

import json
import logging
import subprocess
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Optional, Dict, List

from .business_goals_parser import BusinessGoalsParser
from .task_analyzer import TaskAnalyzer
from .transaction_analyzer import TransactionAnalyzer
from .subscription_detector import SubscriptionDetector
from .briefing_generator import BriefingGenerator
from .entities import BusinessGoals, CompletedTask, Transaction, Subscription

logger = logging.getLogger("weekly_audit")


class AuditOrchestrator:
    """
    Coordinates the weekly audit workflow.

    This class is responsible for:
    1. Collecting data from all sources (Business_Goals.md, /Done, /Accounting)
    2. Analyzing and aggregating data
    3. Preparing context for Claude skill
    4. Invoking the Claude skill to generate the briefing
    5. Verifying the output was created successfully
    """

    def __init__(self, vault_path: Path):
        """
        Initialize the audit orchestrator.

        Args:
            vault_path: Path to the AI Employee Vault directory
        """
        self.vault_path = vault_path
        self.business_goals_path = vault_path / "Business_Goals.md"
        self.done_folder = vault_path / "Done"
        self.accounting_folder = vault_path / "Accounting"
        self.briefings_folder = vault_path / "Briefings"

    def run_weekly_audit(self, week_end: Optional[date] = None) -> Path:
        """
        Execute the complete weekly audit workflow.

        Args:
            week_end: End date of the week to analyze (defaults to today)

        Returns:
            Path to the generated briefing file

        Raises:
            FileNotFoundError: If required directories don't exist
            RuntimeError: If briefing generation fails
        """
        logger.info("Starting weekly audit workflow")

        # Set default week_end to today if not provided
        if week_end is None:
            week_end = date.today()

        week_start = week_end - timedelta(days=6)

        # 1. Validate vault structure
        self._validate_vault_structure()

        # 2. Check for duplicate briefing
        if self._briefing_exists(week_end):
            logger.warning(f"Briefing already exists for {week_end}, skipping generation")
            return self._get_briefing_path(week_end)

        # 3. Parse business goals
        business_goals = self._parse_business_goals()

        # 4. Analyze completed tasks
        completed_tasks = self._analyze_completed_tasks()

        # 5. Parse and summarize transactions
        transactions = self._parse_transactions(week_start, week_end)
        transaction_summary = self._calculate_transaction_summary(transactions, week_start, week_end)

        # 6. Detect subscriptions
        subscriptions = self._detect_subscriptions(transactions, business_goals)

        # 7. Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(completed_tasks)

        # 8. Calculate upcoming deadlines
        upcoming_deadlines = self._calculate_upcoming_deadlines(business_goals, week_end)

        # 9. Generate briefing
        briefing_path = self._generate_briefing(
            week_start,
            week_end,
            business_goals,
            transaction_summary,
            completed_tasks,
            subscriptions,
            bottlenecks,
            upcoming_deadlines
        )

        logger.info(f"Weekly audit completed successfully: {briefing_path}")
        return briefing_path

    def _validate_vault_structure(self):
        """Validate that required vault directories exist."""
        if not self.vault_path.exists():
            raise FileNotFoundError(f"Vault directory not found: {self.vault_path}")

        # Create missing directories
        self.done_folder.mkdir(parents=True, exist_ok=True)
        self.accounting_folder.mkdir(parents=True, exist_ok=True)
        self.briefings_folder.mkdir(parents=True, exist_ok=True)

        logger.info("Vault structure validated")

    def _briefing_exists(self, week_end: date) -> bool:
        """Check if a briefing already exists for the given date."""
        briefing_path = self._get_briefing_path(week_end)
        return briefing_path.exists()

    def _get_briefing_path(self, week_end: date) -> Path:
        """Get the expected path for a briefing file."""
        day_name = week_end.strftime("%A")
        filename = f"{week_end.strftime('%Y-%m-%d')}_{day_name}_Briefing.md"
        return self.briefings_folder / filename

    def _parse_business_goals(self) -> BusinessGoals:
        """Parse business goals from Business_Goals.md."""
        try:
            parser = BusinessGoalsParser(self.business_goals_path)
            return parser.parse()
        except FileNotFoundError:
            logger.warning("Business_Goals.md not found, using defaults")
            # Return default business goals
            return BusinessGoals(
                revenue_target=Decimal("10000.00"),
                current_revenue=Decimal("0.00"),
                key_metrics=[],
                active_projects=[],
                subscription_rules={"inactivity_days": 30, "cost_increase_threshold": 0.20},
                last_updated=date.today(),
                review_frequency="weekly"
            )

    def _analyze_completed_tasks(self) -> List[CompletedTask]:
        """Analyze completed tasks from /Done folder."""
        try:
            analyzer = TaskAnalyzer(self.done_folder)
            return analyzer.analyze_completed_tasks(days=7)
        except FileNotFoundError:
            logger.warning("/Done folder not found, no tasks to analyze")
            return []

    def _parse_transactions(self, start_date: date, end_date: date) -> List[Transaction]:
        """Parse transactions from /Accounting folder."""
        try:
            analyzer = TransactionAnalyzer(self.accounting_folder)
            return analyzer.parse_csv(start_date, end_date)
        except FileNotFoundError:
            logger.warning("/Accounting folder not found, no transactions to analyze")
            return []

    def _calculate_transaction_summary(self, transactions: List[Transaction], start_date: date, end_date: date):
        """Calculate transaction summary."""
        analyzer = TransactionAnalyzer(self.accounting_folder)
        return analyzer.calculate_summary(transactions, start_date, end_date)

    def _detect_subscriptions(self, transactions: List[Transaction], business_goals: BusinessGoals) -> List[Subscription]:
        """Detect subscriptions from transactions."""
        detector = SubscriptionDetector()
        subscriptions = detector.detect_subscriptions(transactions)
        return detector.flag_subscriptions(subscriptions, business_goals.subscription_rules)

    def _identify_bottlenecks(self, completed_tasks: List[CompletedTask]):
        """Identify task bottlenecks."""
        analyzer = TaskAnalyzer(self.done_folder)
        return analyzer.identify_bottlenecks(completed_tasks, threshold=0.5)

    def _calculate_upcoming_deadlines(self, business_goals: BusinessGoals, reference_date: date) -> List[Dict]:
        """Calculate upcoming project deadlines."""
        deadlines = []
        for project in business_goals.active_projects:
            deadline_str = project.get("deadline")
            if deadline_str:
                try:
                    deadline_date = date.fromisoformat(deadline_str)
                    days_remaining = (deadline_date - reference_date).days
                    if days_remaining >= 0 and days_remaining <= 30:
                        deadlines.append({
                            "project": project["name"],
                            "deadline": deadline_str,
                            "days_remaining": days_remaining
                        })
                except (ValueError, KeyError):
                    continue

        # Sort by days remaining (soonest first)
        deadlines.sort(key=lambda d: d["days_remaining"])
        return deadlines

    def _generate_briefing(
        self,
        week_start: date,
        week_end: date,
        business_goals: BusinessGoals,
        transaction_summary,
        completed_tasks: List[CompletedTask],
        subscriptions: List[Subscription],
        bottlenecks,
        upcoming_deadlines: List[Dict]
    ) -> Path:
        """Generate the briefing file."""
        generator = BriefingGenerator(self.briefings_folder)

        # Generate executive summary
        executive_summary = generator.generate_executive_summary(
            transaction_summary,
            completed_tasks,
            subscriptions,
            bottlenecks
        )

        # Generate revenue section
        revenue_section = generator.generate_revenue_section(
            transaction_summary,
            business_goals
        )

        # Generate completed tasks section
        completed_tasks_list = generator.generate_completed_tasks_section(completed_tasks)

        # Generate proactive suggestions
        proactive_suggestions = []
        for subscription in subscriptions:
            if subscription.flags:
                for flag in subscription.flags:
                    suggestion = f"{subscription.name}: {flag}. Consider reviewing to save ${subscription.amount:,.2f}/month."
                    proactive_suggestions.append(suggestion)

        # Write briefing file
        briefing_path = generator.write_briefing_file(
            week_start,
            week_end,
            executive_summary,
            revenue_section,
            completed_tasks_list,
            bottlenecks,
            proactive_suggestions,
            upcoming_deadlines
        )

        return briefing_path


if __name__ == "__main__":
    """Entry point for scheduled task execution."""
    import sys
    from pathlib import Path

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('weekly_audit.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger.info("=" * 60)
    logger.info("Weekly CEO Briefing - Starting Audit")
    logger.info("=" * 60)

    try:
        # Determine vault path (relative to project root)
        project_root = Path(__file__).parent.parent.parent.parent.parent
        vault_path = project_root / "AI_Employee_Vault"

        logger.info(f"Project root: {project_root}")
        logger.info(f"Vault path: {vault_path}")

        if not vault_path.exists():
            logger.error(f"Vault directory not found: {vault_path}")
            sys.exit(1)

        # Create orchestrator and run audit
        orchestrator = AuditOrchestrator(vault_path)
        briefing_path = orchestrator.run_weekly_audit()

        logger.info("=" * 60)
        logger.info(f"SUCCESS: Briefing generated at {briefing_path}")
        logger.info("=" * 60)

        # Write test file to confirm script ran to completion
        test_file = project_root / "weekly_audit_last_run.txt"
        test_file.write_text(
            f"Last successful run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Briefing generated: {briefing_path}\n"
            f"Vault path: {vault_path}\n",
            encoding='utf-8'
        )
        logger.info(f"Test file written: {test_file}")

        sys.exit(0)

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"FAILED: Error generating briefing: {e}")
        logger.error("=" * 60)
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
