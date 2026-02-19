"""
Analyzer for financial transactions from CSV files.

This module reads and analyzes transaction data from the /Accounting folder
to calculate revenue, expenses, and financial summaries.
"""

import csv
import logging
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import List

from .entities import Transaction, TransactionSummary

logger = logging.getLogger("weekly_audit.transaction_analyzer")


class TransactionAnalyzer:
    """
    Analyzer for financial transactions.
    
    Reads CSV files from /Accounting folder and calculates financial summaries.
    Expected CSV format: date, amount, description, category
    """

    def __init__(self, accounting_folder: Path):
        """
        Initialize the transaction analyzer.

        Args:
            accounting_folder: Path to the /Accounting folder
        """
        self.accounting_folder = accounting_folder

    def parse_csv(self, start_date: date, end_date: date) -> List[Transaction]:
        """
        Read and parse all CSV files in the /Accounting folder.

        Args:
            start_date: Start of analysis period
            end_date: End of analysis period

        Returns:
            List of Transaction entities within the date range

        Raises:
            FileNotFoundError: If /Accounting folder doesn't exist
        """
        if not self.accounting_folder.exists():
            logger.error(f"/Accounting folder not found at {self.accounting_folder}")
            raise FileNotFoundError(f"/Accounting folder not found at {self.accounting_folder}")

        logger.info(f"Parsing transactions from {start_date} to {end_date}")

        transactions = []

        # Process all CSV files in the accounting folder
        for csv_file in self.accounting_folder.glob("*.csv"):
            try:
                file_transactions = self._parse_csv_file(csv_file, start_date, end_date)
                transactions.extend(file_transactions)
                logger.debug(f"Parsed {len(file_transactions)} transactions from {csv_file.name}")
            except Exception as e:
                logger.warning(f"Error parsing CSV file {csv_file}: {e}")
                continue

        logger.info(f"Parsed {len(transactions)} total transactions")
        return transactions

    def _parse_csv_file(self, file_path: Path, start_date: date, end_date: date) -> List[Transaction]:
        """
        Parse a single CSV file.

        Args:
            file_path: Path to the CSV file
            start_date: Start of analysis period
            end_date: End of analysis period

        Returns:
            List of Transaction entities from this file
        """
        transactions = []

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Parse transaction date
                    transaction_date = self._parse_date(row['date'])
                    
                    # Filter by date range
                    if start_date <= transaction_date <= end_date:
                        transaction = Transaction(
                            date=transaction_date,
                            amount=Decimal(row['amount']),
                            description=row['description'].strip(),
                            category=row.get('category', 'Uncategorized').strip(),
                            source_file=file_path
                        )
                        transactions.append(transaction)
                        
                except KeyError as e:
                    logger.warning(f"Missing required column in {file_path}: {e}")
                    continue
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid data in {file_path}: {e}")
                    continue

        return transactions

    def _parse_date(self, date_str: str) -> date:
        """
        Parse a date string in YYYY-MM-DD format.

        Args:
            date_str: Date string to parse

        Returns:
            date object

        Raises:
            ValueError: If date format is invalid
        """
        try:
            return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid date format '{date_str}': expected YYYY-MM-DD")

    def calculate_summary(self, transactions: List[Transaction], period_start: date, period_end: date) -> TransactionSummary:
        """
        Calculate financial summary from transactions.

        Args:
            transactions: List of transactions to summarize
            period_start: Start of analysis period
            period_end: End of analysis period

        Returns:
            TransactionSummary entity with aggregated metrics
        """
        logger.info(f"Calculating transaction summary for {len(transactions)} transactions")

        total_revenue = Decimal("0.00")
        total_expenses = Decimal("0.00")
        expense_categories = {}

        for transaction in transactions:
            if transaction.amount > 0:
                # Positive amount = revenue
                total_revenue += transaction.amount
            else:
                # Negative amount = expense
                expense_amount = abs(transaction.amount)
                total_expenses += expense_amount
                
                # Track by category
                category = transaction.category
                if category not in expense_categories:
                    expense_categories[category] = Decimal("0.00")
                expense_categories[category] += expense_amount

        # Calculate net income
        net_income = total_revenue - total_expenses

        # Get top 5 expense categories
        top_categories = sorted(
            [{"category": cat, "amount": amt} for cat, amt in expense_categories.items()],
            key=lambda x: x["amount"],
            reverse=True
        )[:5]

        summary = TransactionSummary(
            total_revenue=total_revenue,
            total_expenses=total_expenses,
            net_income=net_income,
            transaction_count=len(transactions),
            subscription_count=0,  # Will be updated by subscription detector
            top_expense_categories=top_categories,
            period_start=period_start,
            period_end=period_end
        )

        logger.info(f"Summary: Revenue=${total_revenue}, Expenses=${total_expenses}, Net=${net_income}")
        return summary
