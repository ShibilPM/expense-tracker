from datetime import date, datetime
from typing import Optional
import calendar
from config import config


def format_currency(amount: float, currency: str = None) -> str:
    """Format amount as currency string."""
    if currency is None:
        currency = config.DEFAULT_CURRENCY
    return f"{currency}{amount:,.2f}"


def format_date(d: date, fmt: str = None) -> str:
    """Format date according to config."""
    if fmt is None:
        fmt = config.DATE_FORMAT

    if fmt == "DD/MM/YYYY":
        return d.strftime("%d/%m/%Y")
    elif fmt == "MM/DD/YYYY":
        return d.strftime("%m/%d/%Y")
    elif fmt == "YYYY-MM-DD":
        return d.strftime("%Y-%m-%d")
    return d.strftime("%d/%m/%Y")


def parse_date(date_str: str, fmt: str = None) -> Optional[date]:
    """Parse date string to date object."""
    if fmt is None:
        fmt = config.DATE_FORMAT

    try:
        if fmt == "DD/MM/YYYY":
            return datetime.strptime(date_str, "%d/%m/%Y").date()
        elif fmt == "MM/DD/YYYY":
            return datetime.strptime(date_str, "%m/%d/%Y").date()
        elif fmt == "YYYY-MM-DD":
            return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None
    return None


def get_month_range(year: int, month: int) -> tuple:
    """Get first and last date of a month."""
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    return first_day, last_day


def get_previous_month(year: int, month: int) -> tuple:
    """Get previous month (year, month)."""
    if month == 1:
        return year - 1, 12
    return year, month - 1


def get_next_month(year: int, month: int) -> tuple:
    """Get next month (year, month)."""
    if month == 12:
        return year + 1, 1
    return year, month + 1


def month_name(month: int) -> str:
    """Get month name from number."""
    return calendar.month_name[month]


def format_month_year(year: int, month: int) -> str:
    """Format as 'Month Year' (e.g., 'November 2026')."""
    return f"{calendar.month_name[month]} {year}"


def get_current_month() -> tuple:
    """Get current year and month."""
    today = date.today()
    return today.year, today.month


def calculate_percentage_change(current: float, previous: float) -> float:
    """Calculate percentage change between two values."""
    if previous == 0:
        return 0.0 if current == 0 else 100.0
    return ((current - previous) / previous) * 100


def get_week_of_month(d: date) -> int:
    """Get week number within month (1-5)."""
    first_day = date(d.year, d.month, 1)
    dom = d.day
    adjusted_dom = dom + first_day.weekday()
    return (adjusted_dom - 1) // 7 + 1


def validate_amount(amount_str: str) -> Optional[float]:
    """Validate and convert amount string to float.

    Allows positive (expenses) and negative (refunds) amounts.
    Rejects zero and non-numeric values.
    """
    try:
        amount = float(amount_str.replace(",", "").strip())
        if amount == 0:
            return None
        return round(amount, 2)
    except (ValueError, AttributeError):
        return None