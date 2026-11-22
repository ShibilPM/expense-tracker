from datetime import date
from typing import Optional, Tuple
from utils.helpers import validate_amount


def validate_expense_input(amount_str: str, expense_date: date,
                           category_id: int, user_id: int) -> Tuple[bool, str]:
    """
    Validate expense input.
    Returns (is_valid, error_message)
    """
    # Validate amount
    amount = validate_amount(amount_str)
    if amount is None:
        return False, "Please enter a valid amount (positive number)"

    if amount > 1000000:  # 10 lakh limit
        return False, "Amount seems too high. Please verify."

    # Validate date
    if expense_date > date.today():
        return False, "Expense date cannot be in the future"

    # Validate category
    if not category_id or category_id <= 0:
        return False, "Please select a category"

    # Validate user
    if not user_id or user_id <= 0:
        return False, "Invalid user"

    return True, ""


def validate_category_input(name: str, icon: str, color: str) -> Tuple[bool, str]:
    """Validate category input."""
    if not name or not name.strip():
        return False, "Category name is required"

    if len(name.strip()) > 100:
        return False, "Category name too long (max 100 characters)"

    if not icon or not icon.strip():
        return False, "Icon is required"

    # Validate hex color
    if color:
        color = color.strip()
        if not (color.startswith("#") and len(color) == 7):
            return False, "Color must be a valid hex code (e.g., #FF6B6B)"
        try:
            int(color[1:], 16)
        except ValueError:
            return False, "Invalid hex color code"

    return True, ""


def validate_budget_input(amount_str: str, category_id: int, month: str) -> Tuple[bool, str]:
    """Validate budget input."""
    amount = validate_amount(amount_str)
    if amount is None:
        return False, "Please enter a valid budget amount"

    if amount > 1000000:
        return False, "Budget amount seems too high"

    if not category_id or category_id <= 0:
        return False, "Please select a category"

    # Validate month format YYYY-MM
    try:
        year, month_num = map(int, month.split("-"))
        if not (1 <= month_num <= 12) or year < 2020 or year > 2100:
            return False, "Invalid month format (use YYYY-MM)"
    except (ValueError, AttributeError):
        return False, "Invalid month format (use YYYY-MM)"

    return True, ""


def validate_email_config(smtp_host: str, smtp_port: str,
                          email: str, app_password: str, recipient: str) -> Tuple[bool, str]:
    """Validate email configuration."""
    if not smtp_host or not smtp_host.strip():
        return False, "SMTP host is required"

    try:
        port = int(smtp_port)
        if not (1 <= port <= 65535):
            return False, "Invalid SMTP port"
    except ValueError:
        return False, "SMTP port must be a number"

    if not email or "@" not in email:
        return False, "Valid sender email is required"

    if not app_password or len(app_password) < 10:
        return False, "App password is required (16 characters for Gmail)"

    if not recipient or "@" not in recipient:
        return False, "Valid recipient email is required"

    return True, ""