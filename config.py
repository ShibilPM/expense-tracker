import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "expenses.db"


class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
    GMAIL_SMTP_HOST = os.getenv("GMAIL_SMTP_HOST", "smtp.gmail.com")
    GMAIL_SMTP_PORT = int(os.getenv("GMAIL_SMTP_PORT", "587"))
    GMAIL_EMAIL = os.getenv("GMAIL_EMAIL", "")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
    REPORT_RECIPIENT = os.getenv("REPORT_RECIPIENT", "")
    APP_TITLE = os.getenv("APP_TITLE", "Our Expense Tracker")
    DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "₹")
    DATE_FORMAT = os.getenv("DATE_FORMAT", "DD/MM/YYYY")
    TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")


# Default categories (name, icon, color)
DEFAULT_CATEGORIES = [
    ("Food & Dining", "🍔", "#FF6B6B"),
    ("Transport", "🚌", "#4ECDC4"),
    ("Groceries", "🛒", "#45B7D1"),
    ("Rent & Utilities", "🏠", "#96CEB4"),
    ("Entertainment", "🎮", "#FFEAA7"),
    ("Healthcare", "💊", "#DDA0DD"),
    ("Shopping", "🛍️", "#98D8C8"),
    ("Education", "📚", "#F7DC6F"),
    ("Savings/Investment", "💰", "#82E0AA"),
    ("Gifts & Donations", "🎁", "#F8B500"),
    ("Other", "🔧", "#BDC3C7"),
]


config = Config()