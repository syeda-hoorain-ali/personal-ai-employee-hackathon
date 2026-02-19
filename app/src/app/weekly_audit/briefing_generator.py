"""Briefing generator for creating CEO briefing markdown files.

This module provides functionality to generate comprehensive CEO briefings
from collected business data.
"""

import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from .entities import (
    CEOBriefing,
    BusinessGoals,
    TransactionSummary,
    CompletedTask,
    Subscription,
    TaskBottleneck,
)

logger = logging.getLogger("weekly_audit.briefing_generator")


class BriefingGenerator:
    """Generator for CEO briefing markdown files."""

    def __init__(self, briefings_folder: Path):
        """Initialize the briefing generator.

        Args:
            briefings_folder: Path to the Briefings folder for output
        """
        self.briefings_folder = briefings_folder
        self.briefings_folder.mkdir(parents=True, exist_ok=True)

    def generate_briefing(self, briefing_data: CEOBriefing) -> Optional[str]:
        """Generate complete CEO briefing from data.

        Args:
            briefing_data: CEOBriefing instance with all data

        Returns:
            Path to generated briefing file, or None if generation failed
        """
        try:
            # Generate briefing sections
            executive_summary = self.generate_executive_summary(briefing_data)
            revenue_section = self.generate_revenue_section(briefing_data)
            completed_tasks_section = self.generate_completed_tasks_section(briefing_data.completed_tasks)
            suggestions_section = self.generate_proactive_suggestions(briefing_data.subscriptions)
            bottlenecks_section = self.generate_bottlenecks_section(briefing_data.bottlenecks)

            # Combine all sections
            briefing_content = self._assemble_briefing(
                briefing_data,
                executive_summary,
                revenue_section,
                completed_tasks_section,
                suggestions_section,
                bottlenecks_section,
            )

            # Write briefing file
            output_path = self.write_briefing_file(briefing_data.week_start, briefing_content)

            logger.info(f"Successfully generated briefing at {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate briefing: {e}", exc_info=True)
            return None

    def generate_executive_summary(
        self,
        transaction_summary,
        completed_tasks,
        subscriptions,
        bottlenecks
    ) -> str:
        """Generate 2-3 sentence executive summary.

        Args:
            transaction_summary: TransactionSummary entity
            completed_tasks: List of CompletedTask entities
            subscriptions: List of Subscription entities
            bottlenecks: List of TaskBottleneck entities

        Returns:
            Executive summary text
        """
        tasks_count = len(completed_tasks)

        # Build summary
        summary_text = (
            f"This week the team completed {tasks_count} task{'s' if tasks_count != 1 else ''} "
            f"and generated ${transaction_summary.total_revenue:,.2f} in revenue. "
        )

        # Add bottleneck or subscription insight if available
        if bottlenecks:
            summary_text += f"Process analysis identified {len(bottlenecks)} task bottleneck{'s' if len(bottlenecks) != 1 else ''} requiring attention."
        elif subscriptions:
            flagged = [s for s in subscriptions if s.flags]
            if flagged:
                summary_text += f"Cost optimization analysis flagged {len(flagged)} subscription{'s' if len(flagged) != 1 else ''} for review."
        else:
            summary_text += "Operations are running efficiently with no significant issues identified."

        return summary_text

    def generate_revenue_section(
        self,
        transaction_summary,
        business_goals
    ) -> str:
        """Generate revenue and financial metrics section.

        Args:
            transaction_summary: TransactionSummary entity
            business_goals: BusinessGoals entity

        Returns:
            Revenue section markdown
        """
        section = "## Financial Performance\n\n"
        section += "### Revenue & Expenses\n"
        section += f"- **Total Revenue**: ${transaction_summary.total_revenue:,.2f}\n"
        section += f"- **Total Expenses**: ${transaction_summary.total_expenses:,.2f}\n"
        section += f"- **Net Income**: ${transaction_summary.net_income:,.2f}\n"
        section += f"- **Transaction Count**: {transaction_summary.transaction_count}\n\n"

        # Add revenue target comparison
        section += "### Revenue Target\n"
        section += f"- **Monthly Target**: ${business_goals.revenue_target:,.2f}\n"
        section += f"- **Current Revenue**: ${business_goals.current_revenue:,.2f}\n\n"

        return section

        return section

    def generate_completed_tasks_section(self, tasks: list[CompletedTask]) -> str:
        """Generate completed tasks section.

        Args:
            tasks: List of completed tasks

        Returns:
            Completed tasks section markdown
        """
        if not tasks:
            return "## Completed Work\n\nNo tasks completed this week.\n\n"

        section = "## Completed Work\n\n"
        section += f"### Tasks Completed This Week ({len(tasks)} total)\n\n"

        # Group tasks by project if available
        projects = {}
        for task in tasks:
            project = task.project or "General"
            if project not in projects:
                projects[project] = []
            projects[project].append(task)

        # Generate task list by project
        for project, project_tasks in sorted(projects.items()):
            if len(projects) > 1:
                section += f"**{project}**\n"

            for task in sorted(project_tasks, key=lambda t: t.completion_date, reverse=True):
                date_str = task.completion_date.strftime("%b %d")
                priority_str = f" [{task.priority}]" if task.priority else ""
                section += f"- {task.title}{priority_str} - Completed {date_str}\n"

            section += "\n"

        return section

    def generate_proactive_suggestions(self, subscriptions: list[Subscription]) -> str:
        """Generate proactive suggestions section for cost optimization.

        Args:
            subscriptions: List of detected subscriptions

        Returns:
            Proactive suggestions section markdown
        """
        flagged_subscriptions = [s for s in subscriptions if s.flags]

        if not flagged_subscriptions:
            return "## Proactive Suggestions\n\nNo cost optimization opportunities identified this week.\n\n"

        section = "## Proactive Suggestions\n\n"
        section += "### Cost Optimization Opportunities\n\n"
        section += "| Service | Monthly Cost | Issue | Recommendation |\n"
        section += "|---------|-------------|-------|----------------|\n"

        for sub in flagged_subscriptions:
            issue = ", ".join(sub.flags).replace("_", " ").title()
            recommendation = self._get_subscription_recommendation(sub)
            section += f"| {sub.name} | ${sub.amount:.2f} | {issue} | {recommendation} |\n"

        section += "\n"
        return section

    def _get_subscription_recommendation(self, subscription: Subscription) -> str:
        """Get recommendation text for a flagged subscription.

        Args:
            subscription: Subscription instance

        Returns:
            Recommendation text
        """
        if "no_activity_30_days" in subscription.flags:
            return "Review usage and consider canceling"
        elif "cost_increase_20_percent" in subscription.flags:
            return "Investigate price increase and evaluate alternatives"
        else:
            return "Review subscription necessity"

    def generate_bottlenecks_section(self, bottlenecks: list[TaskBottleneck]) -> str:
        """Generate task bottlenecks section.

        Args:
            bottlenecks: List of task bottlenecks

        Returns:
            Bottlenecks section markdown
        """
        if not bottlenecks:
            return "## Process Insights\n\nNo significant task delays identified this week.\n\n"

        section = "## Process Insights\n\n"
        section += "### Task Bottlenecks\n\n"
        section += "| Task | Expected | Actual | Delay |\n"
        section += "|------|----------|--------|-------|\n"

        for bottleneck in bottlenecks:
            section += (
                f"| {bottleneck.task} | {bottleneck.expected_duration} | "
                f"{bottleneck.actual_duration} | {bottleneck.delay_percent:.0f}% |\n"
            )

        section += "\n"

        # Add analysis
        if len(bottlenecks) > 2:
            section += "**Analysis**: Multiple tasks experienced significant delays. "
            section += "Consider reviewing estimation accuracy and identifying common blockers.\n\n"
        else:
            section += "**Analysis**: Limited delays observed. Monitor these tasks for patterns.\n\n"

        return section

    def _assemble_briefing(
        self,
        briefing_data: CEOBriefing,
        executive_summary: str,
        revenue_section: str,
        completed_tasks_section: str,
        suggestions_section: str,
        bottlenecks_section: str,
    ) -> str:
        """Assemble complete briefing from sections.

        Args:
            briefing_data: CEOBriefing instance
            executive_summary: Executive summary text
            revenue_section: Revenue section markdown
            completed_tasks_section: Completed tasks section markdown
            suggestions_section: Proactive suggestions section markdown
            bottlenecks_section: Bottlenecks section markdown

        Returns:
            Complete briefing markdown
        """
        week_start_str = briefing_data.week_start.strftime("%B %d, %Y")
        week_end_str = briefing_data.week_end.strftime("%B %d, %Y")
        generated_str = briefing_data.generated_at.strftime("%Y-%m-%d %H:%M:%S")

        briefing = f"# Monday Morning CEO Briefing\n"
        briefing += f"**Week of**: {week_start_str} - {week_end_str}\n"
        briefing += f"**Generated**: {generated_str}\n\n"
        briefing += "---\n\n"
        briefing += "## Executive Summary\n\n"
        briefing += f"{executive_summary}\n\n"
        briefing += "---\n\n"
        briefing += revenue_section
        briefing += "---\n\n"
        briefing += completed_tasks_section
        briefing += "---\n\n"
        briefing += suggestions_section
        briefing += "---\n\n"
        briefing += bottlenecks_section
        briefing += "---\n\n"
        briefing += "*This briefing was automatically generated by your AI Employee. "
        briefing += "Data sources: Business Goals, Task Tracker, Accounting Records.*\n"

        return briefing

    def write_briefing_file(
        self,
        week_start,
        week_end,
        executive_summary,
        revenue_section,
        completed_tasks_list,
        bottlenecks,
        proactive_suggestions,
        upcoming_deadlines
    ) -> str:
        """Write briefing content to file.

        Args:
            week_start: Start date of the week
            week_end: End date of the week
            executive_summary: Executive summary text
            revenue_section: Revenue section markdown
            completed_tasks_list: Completed tasks section markdown
            bottlenecks: List of TaskBottleneck entities
            proactive_suggestions: List of suggestion strings
            upcoming_deadlines: List of deadline dicts

        Returns:
            Path to the created briefing file
        """
        # Assemble briefing content
        content = f"# Weekly CEO Briefing\n\n"
        content += f"**Week of {week_start.strftime('%B %d, %Y')} - {week_end.strftime('%B %d, %Y')}**\n\n"
        content += f"---\n\n"

        # Executive Summary
        content += f"## Executive Summary\n\n{executive_summary}\n\n"
        content += f"---\n\n"

        # Revenue Section
        content += revenue_section
        content += f"---\n\n"

        # Completed Tasks
        content += completed_tasks_list
        content += f"---\n\n"

        # Proactive Suggestions
        if proactive_suggestions:
            content += f"## Proactive Suggestions\n\n"
            for suggestion in proactive_suggestions:
                content += f"- {suggestion}\n"
            content += f"\n---\n\n"

        # Task Bottlenecks
        if bottlenecks:
            content += f"## Task Bottlenecks\n\n"
            content += f"Tasks that took significantly longer than expected:\n\n"
            content += f"| Task | Expected | Actual | Delay |\n"
            content += f"|------|----------|--------|-------|\n"
            for bottleneck in bottlenecks:
                expected_hours = bottleneck.expected_duration.total_seconds() / 3600
                actual_hours = bottleneck.actual_duration.total_seconds() / 3600
                content += f"| {bottleneck.task_name} | {expected_hours:.1f}h | {actual_hours:.1f}h | {bottleneck.delay_percent:.0f}% |\n"
            content += f"\n---\n\n"

        # Upcoming Deadlines
        if upcoming_deadlines:
            content += f"## Upcoming Deadlines\n\n"
            for deadline in upcoming_deadlines:
                content += f"- **{deadline['project']}**: {deadline['deadline']} ({deadline['days_remaining']} days remaining)\n"
            content += f"\n---\n\n"

        # Footer
        content += f"*This briefing was automatically generated by your AI Employee.*\n"
        content += f"*Data sources: Business Goals, Task Tracker, Accounting Records.*\n"

        # Generate filename: YYYY-MM-DD_DayOfWeek_Briefing.md
        day_name = week_end.strftime('%A')
        filename = f"{week_end.strftime('%Y-%m-%d')}_{day_name}_Briefing.md"
        output_path = self.briefings_folder / filename

        # Write content
        output_path.write_text(content, encoding="utf-8")

        logger.info(f"Wrote briefing to {output_path}")
        return str(output_path)
