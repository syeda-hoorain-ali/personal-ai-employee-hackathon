"""Subscription detector for identifying recurring subscription services.

This module provides functionality to detect subscription patterns from
transaction data and flag subscriptions that may need attention.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict

from .entities import Transaction, Subscription

logger = logging.getLogger("weekly_audit.subscription_detector")


# Common subscription service patterns
SUBSCRIPTION_PATTERNS = {
    "netflix": ["netflix", "nflx"],
    "spotify": ["spotify"],
    "github": ["github"],
    "adobe": ["adobe", "creative cloud"],
    "notion": ["notion"],
    "slack": ["slack"],
    "openai": ["openai", "chatgpt"],
    "microsoft": ["microsoft 365", "office 365", "ms365"],
    "google": ["google workspace", "g suite", "google one"],
    "dropbox": ["dropbox"],
    "zoom": ["zoom"],
    "aws": ["amazon web services", "aws"],
    "heroku": ["heroku"],
    "digitalocean": ["digitalocean"],
    "vercel": ["vercel"],
    "cloudflare": ["cloudflare"],
    "mailchimp": ["mailchimp"],
    "hubspot": ["hubspot"],
    "salesforce": ["salesforce"],
    "zendesk": ["zendesk"],
    "intercom": ["intercom"],
    "stripe": ["stripe"],
    "twilio": ["twilio"],
    "sendgrid": ["sendgrid"],
}


class SubscriptionDetector:
    """Detector for recurring subscription services."""

    def __init__(self):
        """Initialize the subscription detector."""
        self.subscription_patterns = SUBSCRIPTION_PATTERNS

    def detect_subscriptions(
        self,
        transactions: list[Transaction],
        min_occurrences: int = 2,
        amount_variance_threshold: float = 0.10,
        frequency_range: tuple[int, int] = (25, 35),
    ) -> list[Subscription]:
        """Detect subscriptions from transaction patterns.

        Uses hybrid pattern matching + recurrence analysis:
        - Pattern matching: Identifies known subscription services
        - Recurrence analysis: Detects recurring charges with similar amounts

        Args:
            transactions: List of transactions to analyze
            min_occurrences: Minimum number of occurrences to consider (default: 2)
            amount_variance_threshold: Maximum amount variance as percentage (default: 0.10 = 10%)
            frequency_range: Expected frequency range in days (default: 25-35 for monthly)

        Returns:
            List of detected Subscription instances
        """
        if not transactions:
            logger.info("No transactions to analyze for subscriptions")
            return []

        # Filter expense transactions only
        expenses = [t for t in transactions if t.amount < 0]

        if not expenses:
            logger.info("No expense transactions found")
            return []

        # Group transactions by description pattern
        grouped_transactions = self._group_transactions_by_pattern(expenses)

        # Detect subscriptions from grouped transactions
        subscriptions = []

        for pattern_key, pattern_transactions in grouped_transactions.items():
            if len(pattern_transactions) < min_occurrences:
                continue

            # Analyze recurrence pattern
            subscription = self._analyze_recurrence_pattern(
                pattern_key,
                pattern_transactions,
                amount_variance_threshold,
                frequency_range,
            )

            if subscription:
                subscriptions.append(subscription)
                logger.debug(f"Detected subscription: {subscription.name}")

        logger.info(f"Detected {len(subscriptions)} subscriptions")
        return subscriptions

    def _group_transactions_by_pattern(
        self, transactions: list[Transaction]
    ) -> dict[str, list[Transaction]]:
        """Group transactions by matching subscription patterns.

        Args:
            transactions: List of transactions to group

        Returns:
            Dictionary mapping pattern keys to lists of matching transactions
        """
        grouped = defaultdict(list)

        for transaction in transactions:
            description_lower = transaction.description.lower()

            # Try to match known subscription patterns
            matched = False
            for service_name, patterns in self.subscription_patterns.items():
                for pattern in patterns:
                    if pattern in description_lower:
                        grouped[service_name].append(transaction)
                        matched = True
                        break
                if matched:
                    break

            # If no pattern matched, group by exact description
            if not matched:
                # Normalize description for grouping
                normalized = description_lower.strip()
                grouped[normalized].append(transaction)

        return dict(grouped)

    def _analyze_recurrence_pattern(
        self,
        pattern_key: str,
        transactions: list[Transaction],
        amount_variance_threshold: float,
        frequency_range: tuple[int, int],
    ) -> Optional[Subscription]:
        """Analyze transactions to determine if they represent a subscription.

        Args:
            pattern_key: Pattern key (service name or description)
            transactions: List of transactions matching the pattern
            amount_variance_threshold: Maximum amount variance threshold
            frequency_range: Expected frequency range in days

        Returns:
            Subscription instance if pattern matches, None otherwise
        """
        if len(transactions) < 2:
            return None

        # Sort transactions by date
        sorted_transactions = sorted(transactions, key=lambda t: t.date)

        # Calculate average amount
        amounts = [abs(t.amount) for t in sorted_transactions]
        avg_amount = sum(amounts) / len(amounts)

        # Check amount variance
        max_variance = max(abs(amt - avg_amount) / avg_amount for amt in amounts)
        if max_variance > amount_variance_threshold:
            logger.debug(
                f"Pattern '{pattern_key}' rejected: amount variance {max_variance:.2%} "
                f"exceeds threshold {amount_variance_threshold:.2%}"
            )
            return None

        # Calculate average frequency (days between charges)
        if len(sorted_transactions) >= 2:
            intervals = []
            for i in range(1, len(sorted_transactions)):
                interval = (sorted_transactions[i].date - sorted_transactions[i - 1].date).days
                intervals.append(interval)

            avg_frequency = sum(intervals) / len(intervals)

            # Check if frequency is within expected range
            min_freq, max_freq = frequency_range
            if not (min_freq <= avg_frequency <= max_freq):
                logger.debug(
                    f"Pattern '{pattern_key}' rejected: frequency {avg_frequency:.1f} days "
                    f"outside range {min_freq}-{max_freq}"
                )
                return None

            frequency = "monthly"
        else:
            avg_frequency = 30
            frequency = "monthly"

        # Create subscription
        last_transaction = sorted_transactions[-1]

        # Determine service name
        service_name = pattern_key.replace("_", " ").title()
        if pattern_key in self.subscription_patterns:
            service_name = pattern_key.title()

        subscription = Subscription(
            name=service_name,
            amount=avg_amount,
            last_seen_date=last_transaction.date,
            frequency=frequency,
            pattern_matched=pattern_key,
            transaction_count=len(sorted_transactions),
            flags=[],
        )

        return subscription

    def flag_subscriptions(
        self,
        subscriptions: list[Subscription],
        no_activity_days: int = 30,
        cost_increase_threshold: float = 0.20,
    ) -> list[Subscription]:
        """Flag subscriptions that may need attention.

        Flags:
        - no_activity_30_days: No charges in the last 30+ days
        - cost_increase_20_percent: Cost increased by 20%+ (requires historical data)

        Args:
            subscriptions: List of subscriptions to flag
            no_activity_days: Days threshold for no activity flag (default: 30)
            cost_increase_threshold: Cost increase threshold (default: 0.20 = 20%)

        Returns:
            List of subscriptions with flags added
        """
        if not subscriptions:
            return []

        flagged_subscriptions = []
        current_date = datetime.now().date()

        for subscription in subscriptions:
            flags = []

            # Check for no activity
            days_since_last_charge = (current_date - subscription.last_seen_date).days
            if days_since_last_charge >= no_activity_days:
                flags.append("no_activity_30_days")
                logger.debug(
                    f"Subscription '{subscription.name}' flagged: "
                    f"no activity for {days_since_last_charge} days"
                )

            # Note: Cost increase detection requires historical data
            # This would need to be implemented with a subscription history database
            # For now, we skip this flag

            # Create new subscription with flags
            flagged_subscription = Subscription(
                name=subscription.name,
                amount=subscription.amount,
                last_seen_date=subscription.last_seen_date,
                frequency=subscription.frequency,
                pattern_matched=subscription.pattern_matched,
                transaction_count=subscription.transaction_count,
                flags=flags,
            )

            flagged_subscriptions.append(flagged_subscription)

        flagged_count = sum(1 for s in flagged_subscriptions if s.flags)
        logger.info(f"Flagged {flagged_count} subscriptions out of {len(subscriptions)}")

        return flagged_subscriptions
