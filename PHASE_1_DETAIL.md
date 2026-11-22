# Phase 1 Detailed Breakdown: Project Setup & Database Foundation

## Files to Create

### 1. `requirements.txt`
```txt
streamlit>=1.35.0
sqlalchemy>=2.0.0
pandas>=2.2.0
plotly>=5.20.0
apscheduler>=3.10.0
python-dotenv>=1.0.0
openpyxl>=3.1.0
reportlab>=4.0.0
kaleido>=0.1.0
python-dateutil>=2.9.0
alembic>=1.13.0
```

### 2. `.env.example` (template for environment variables)
```env
# Database
DATABASE_URL=sqlite:///expenses.db

# Gmail SMTP (create App Password at: myaccount.google.com/apppasswords)
GMAIL_SMTP_HOST=smtp.gmail.com
GMAIL_SMTP_PORT=587
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password
REPORT_RECIPIENT=partner-email@gmail.com

# App Settings
APP_TITLE=Our Expense Tracker
DEFAULT_CURRENCY=₹
DATE_FORMAT=DD/MM/YYYY
TIMEZONE=Asia/Kolkata
```

### 3. `config.py` - Central configuration
```python
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
```

### 4. `database/models.py` - SQLAlchemy Models
```python
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, 
    ForeignKey, Boolean, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    expenses = relationship("Expense", back_populates="user", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    email_config = relationship("EmailConfig", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    icon = Column(String(10), default="🔧")
    color = Column(String(7), default="#BDC3C7")  # Hex color
    is_default = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)  # Null = global
    
    user = relationship("User", back_populates="categories")
    expenses = relationship("Expense", back_populates="category")
    
    __table_args__ = (
        UniqueConstraint("name", "user_id", name="uq_category_name_user"),
    )

class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False, index=True)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="expenses")
    category = relationship("Category", back_populates="expenses")
    
    __table_args__ = (
        Index("ix_expenses_user_date", "user_id", "date"),
    )

class Budget(Base):
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    month = Column(String(7), nullable=False)  # Format: YYYY-MM
    amount = Column(Float, nullable=False)
    alert_threshold = Column(Float, default=0.8)  # 80% default
    
    user = relationship("User", back_populates="budgets")
    category = relationship("Category")
    
    __table_args__ = (
        UniqueConstraint("user_id", "category_id", "month", name="uq_budget_user_cat_month"),
    )

class EmailConfig(Base):
    __tablename__ = "email_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    smtp_host = Column(String(255), default="smtp.gmail.com")
    smtp_port = Column(Integer, default=587)
    email = Column(String(255), nullable=False)
    app_password = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    is_enabled = Column(Boolean, default=False)
    last_sent = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="email_config")
```

### 5. `database/init_db.py` - Database Initialization
```python
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from config import config, DEFAULT_CATEGORIES
from database.models import Base, User, Category

def init_database():
    """Create database tables and seed default data."""
    engine = create_engine(config.DATABASE_URL, echo=False)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create default users if not exist
        users = ["You", "Husband"]
        for name in users:
            if not session.query(User).filter_by(name=name).first():
                user = User(name=name)
                session.add(user)
        session.commit()
        
        # Seed global default categories
        for name, icon, color in DEFAULT_CATEGORIES:
            if not session.query(Category).filter_by(name=name, user_id=None).first():
                cat = Category(name=name, icon=icon, color=color, is_default=True, user_id=None)
                session.add(cat)
        session.commit()
        
        print("✅ Database initialized successfully!")
        print(f"📍 Database location: {config.DATABASE_URL}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error initializing database: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    init_database()
```

### 6. `database/crud.py` - Database Operations
```python
from datetime import date, datetime
from typing import List, Optional, Tuple
from sqlalchemy import create_engine, func, and_, or_, extract
from sqlalchemy.orm import sessionmaker, Session as SessionType
from contextlib import contextmanager

from config import config
from database.models import Base, User, Category, Expense, Budget, EmailConfig

engine = create_engine(config.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

@contextmanager
def get_session() -> SessionType:
    """Context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# ========== USER OPERATIONS ==========
def get_users(active_only: bool = True) -> List[User]:
    with get_session() as session:
        query = session.query(User)
        if active_only:
            query = query.filter(User.is_active == True)
        return query.order_by(User.name).all()

def get_user_by_name(name: str) -> Optional[User]:
    with get_session() as session:
        return session.query(User).filter(User.name == name).first()

def create_user(name: str, email: str = None) -> User:
    with get_session() as session:
        user = User(name=name, email=email)
        session.add(user)
        session.flush()
        return user

# ========== CATEGORY OPERATIONS ==========
def get_categories(user_id: Optional[int] = None) -> List[Category]:
    """Get categories for a user (includes global categories)."""
    with get_session() as session:
        query = session.query(Category).filter(
            or_(Category.user_id == user_id, Category.user_id.is_(None))
        )
        return query.order_by(Category.is_default.desc(), Category.name).all()

def get_category_by_id(cat_id: int) -> Optional[Category]:
    with get_session() as session:
        return session.query(Category).filter(Category.id == cat_id).first()

def create_category(name: str, icon: str, color: str, user_id: Optional[int] = None) -> Category:
    with get_session() as session:
        cat = Category(name=name, icon=icon, color=color, user_id=user_id)
        session.add(cat)
        session.flush()
        return cat

def update_category(cat_id: int, **kwargs) -> Optional[Category]:
    with get_session() as session:
        cat = session.query(Category).filter(Category.id == cat_id).first()
        if cat:
            for key, value in kwargs.items():
                setattr(cat, key, value)
        return cat

def delete_category(cat_id: int) -> bool:
    with get_session() as session:
        cat = session.query(Category).filter(Category.id == cat_id).first()
        if cat and not cat.is_default:
            session.delete(cat)
            return True
        return False

# ========== EXPENSE OPERATIONS ==========
def create_expense(user_id: int, category_id: int, amount: float, 
                   expense_date: date, notes: str = None) -> Expense:
    with get_session() as session:
        expense = Expense(
            user_id=user_id,
            category_id=category_id,
            amount=amount,
            date=expense_date,
            notes=notes
        )
        session.add(expense)
        session.flush()
        return expense

def get_expenses(user_id: Optional[int] = None, 
                 start_date: Optional[date] = None,
                 end_date: Optional[date] = None,
                 category_id: Optional[int] = None) -> List[Expense]:
    with get_session() as session:
        query = session.query(Expense)
        if user_id:
            query = query.filter(Expense.user_id == user_id)
        if start_date:
            query = query.filter(Expense.date >= start_date)
        if end_date:
            query = query.filter(Expense.date <= end_date)
        if category_id:
            query = query.filter(Expense.category_id == category_id)
        return query.order_by(Expense.date.desc(), Expense.created_at.desc()).all()

def get_expense_by_id(expense_id: int) -> Optional[Expense]:
    with get_session() as session:
        return session.query(Expense).filter(Expense.id == expense_id).first()

def update_expense(expense_id: int, **kwargs) -> Optional[Expense]:
    with get_session() as session:
        expense = session.query(Expense).filter(Expense.id == expense_id).first()
        if expense:
            for key, value in kwargs.items():
                setattr(expense, key, value)
            expense.updated_at = datetime.utcnow()
        return expense

def delete_expense(expense_id: int) -> bool:
    with get_session() as session:
        expense = session.query(Expense).filter(Expense.id == expense_id).first()
        if expense:
            session.delete(expense)
            return True
        return False

# ========== AGGREGATION QUERIES ==========
def get_monthly_total(user_id: int, year: int, month: int) -> float:
    with get_session() as session:
        result = session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == user_id,
            extract('year', Expense.date) == year,
            extract('month', Expense.date) == month
        ).scalar()
        return float(result) if result else 0.0

def get_category_spending(user_id: int, year: int, month: int) -> List[Tuple]:
    """Returns list of (category_name, icon, color, total_amount)"""
    with get_session() as session:
        results = session.query(
            Category.name, Category.icon, Category.color,
            func.sum(Expense.amount).label('total')
        ).join(Expense).filter(
            Expense.user_id == user_id,
            extract('year', Expense.date) == year,
            extract('month', Expense.date) == month
        ).group_by(Category.id, Category.name, Category.icon, Category.color).all()
        return [(r.name, r.icon, r.color, float(r.total)) for r in results]

def get_daily_spending(user_id: int, year: int, month: int) -> List[Tuple]:
    """Returns list of (date, total_amount) for each day in month"""
    with get_session() as session:
        results = session.query(
            Expense.date, func.sum(Expense.amount).label('total')
        ).filter(
            Expense.user_id == user_id,
            extract('year', Expense.date) == year,
            extract('month', Expense.date) == month
        ).group_by(Expense.date).order_by(Expense.date).all()
        return [(r.date, float(r.total)) for r in results]

# ========== BUDGET OPERATIONS ==========
def set_budget(user_id: int, category_id: int, month: str, amount: float, 
               alert_threshold: float = 0.8) -> Budget:
    with get_session() as session:
        budget = session.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.category_id == category_id,
            Budget.month == month
        ).first()
        if budget:
            budget.amount = amount
            budget.alert_threshold = alert_threshold
        else:
            budget = Budget(
                user_id=user_id,
                category_id=category_id,
                month=month,
                amount=amount,
                alert_threshold=alert_threshold
            )
            session.add(budget)
        session.flush()
        return budget

def get_budgets(user_id: int, month: str) -> List[Budget]:
    with get_session() as session:
        return session.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.month == month
        ).all()

# ========== EMAIL CONFIG OPERATIONS ==========
def get_email_config(user_id: int) -> Optional[EmailConfig]:
    with get_session() as session:
        return session.query(EmailConfig).filter(EmailConfig.user_id == user_id).first()

def upsert_email_config(user_id: int, smtp_host: str, smtp_port: int,
                        email: str, app_password: str, recipient_email: str,
                        is_enabled: bool = False) -> EmailConfig:
    with get_session() as session:
        config = session.query(EmailConfig).filter(EmailConfig.user_id == user_id).first()
        if config:
            config.smtp_host = smtp_host
            config.smtp_port = smtp_port
            config.email = email
            config.app_password = app_password
            config.recipient_email = recipient_email
            config.is_enabled = is_enabled
        else:
            config = EmailConfig(
                user_id=user_id,
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                email=email,
                app_password=app_password,
                recipient_email=recipient_email,
                is_enabled=is_enabled
            )
            session.add(config)
        session.flush()
        return config
```

### 7. `app.py` - Main Entry Point
```python
import streamlit as st
from pathlib import Path

# Page config - MUST be first Streamlit command
st.set_page_config(
    page_title="Our Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database on first run
from database.init_db import init_database
if not Path("expenses.db").exists():
    with st.spinner("Initializing database..."):
        init_database()

# Sidebar - User selection
from database.crud import get_users
users = get_users()
user_names = [u.name for u in users]

if "current_user" not in st.session_state:
    st.session_state.current_user = user_names[0] if user_names else "You"

st.sidebar.title("👤 Current User")
selected_user = st.sidebar.selectbox(
    "Select user",
    user_names,
    index=user_names.index(st.session_state.current_user) if st.session_state.current_user in user_names else 0
)
st.session_state.current_user = selected_user

# Get user ID for queries
from database.crud import get_user_by_name
current_user_obj = get_user_by_name(selected_user)
st.session_state.current_user_id = current_user_obj.id if current_user_obj else None

# Navigation
st.sidebar.title("📱 Navigation")
pages = {
    "📝 Log Expense": "pages/1_📝_Log_Expense.py",
    "📊 Dashboard": "pages/2_📊_Dashboard.py",
    "📈 Monthly Summary": "pages/3_📈_Monthly_Summary.py",
    "⚙️ Settings": "pages/4_⚙️_Settings.py",
    "👥 Users": "pages/5_👥_Users.py",
}

for label, path in pages.items():
    if st.sidebar.button(label, use_container_width=True):
        st.switch_page(path)

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("💰 Our Expense Tracker v1.0")
```

### 8. `.gitignore`
```gitignore
# Database
*.db
*.sqlite
*.sqlite3

# Environment
.env
.env.local

# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.coverage
htmlcov/

# Virtual environment
venv/
env/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Streamlit
.streamlit/secrets.toml

# Exports
exports/
*.xlsx
*.pdf
```

---

## Phase 1 Verification Checklist

Run these commands to verify everything works:

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy .env.example to .env and fill in values
copy .env.example .env

# 4. Initialize database
python database/init_db.py

# 5. Run the app
streamlit run app.py
```

**Expected outcome:**
- Browser opens at `http://localhost:8501`
- Sidebar shows user selector ("You" / "Husband")
- Navigation buttons for 5 pages (pages will be empty but navigable)
- Database file `expenses.db` created with tables and default data

---

## Next: Phase 2 Preview

Once Phase 1 is verified, Phase 2 will build:
1. **Log Expense page** - Date picker, amount, category dropdown, notes, save button
2. **Expense list** - View/edit/delete logged expenses
3. **Category management** in Settings page
4. **Input validation** and toast notifications

---

Ready to start Phase 1 implementation?