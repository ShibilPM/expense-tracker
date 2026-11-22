from datetime import date, datetime
from typing import List, Optional, Tuple
from sqlalchemy import create_engine, func, and_, or_, extract
from sqlalchemy.orm import sessionmaker, Session as SessionType
from contextlib import contextmanager

from config import config
from database.models import Base, User, Category, Expense, Budget, EmailConfig

engine = create_engine(config.DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


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
    """Get users - returns User objects but session must stay open."""
    session = SessionLocal()
    try:
        query = session.query(User)
        if active_only:
            query = query.filter(User.is_active == True)
        return query.order_by(User.name).all()
    finally:
        session.close()


def get_user_names(active_only: bool = True) -> List[str]:
    """Get just user names - safe to use after session closes."""
    session = SessionLocal()
    try:
        query = session.query(User.name)
        if active_only:
            query = query.filter(User.is_active == True)
        return [row[0] for row in query.order_by(User.name).all()]
    finally:
        session.close()


def get_user_by_name(name: str) -> Optional[User]:
    """Get user by name - NOTE: session must be open for full User object."""
    session = SessionLocal()
    try:
        return session.query(User).filter(User.name == name).first()
    finally:
        session.close()


def get_user_id_by_name(name: str) -> Optional[int]:
    """Get user ID by name - safe to use after session closes."""
    session = SessionLocal()
    try:
        result = session.query(User.id).filter(User.name == name).scalar()
        return result
    finally:
        session.close()


def get_user_by_id(user_id: int) -> Optional[User]:
    with get_session() as session:
        return session.query(User).filter(User.id == user_id).first()


def create_user(name: str, email: str = None) -> User:
    with get_session() as session:
        user = User(name=name, email=email)
        session.add(user)
        session.flush()
        return user


def update_user(user_id: int, **kwargs) -> Optional[User]:
    with get_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            for key, value in kwargs.items():
                setattr(user, key, value)
        return user


def delete_user(user_id: int) -> bool:
    """Soft delete a user - sets is_active to False.
    User will not appear in selector, but their expenses/budgets remain.
    """
    with get_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user and user.is_active:
            user.is_active = False
            session.flush()
            return True
        return False


def restore_user(user_id: int) -> bool:
    """Restore a soft-deleted user - sets is_active to True."""
    with get_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user or user.is_active:
            return False
        user.is_active = True
        session.flush()
        return True


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


def get_weekly_spending(user_id: int, year: int, month: int) -> List[Tuple]:
    """Returns list of (week_number, total_amount) for each week in month"""
    with get_session() as session:
        results = session.query(
            func.strftime('%W', Expense.date).label('week'),
            func.sum(Expense.amount).label('total')
        ).filter(
            Expense.user_id == user_id,
            extract('year', Expense.date) == year,
            extract('month', Expense.date) == month
        ).group_by('week').order_by('week').all()
        return [(int(r.week), float(r.total)) for r in results]


def get_expenses_by_category_and_date(user_id: int, year: int, month: int) -> List[Tuple]:
    """Returns list of (date, category_name, icon, color, amount) for heatmap"""
    with get_session() as session:
        results = session.query(
            Expense.date, Category.name, Category.icon, Category.color,
            func.sum(Expense.amount).label('total')
        ).join(Category).filter(
            Expense.user_id == user_id,
            extract('year', Expense.date) == year,
            extract('month', Expense.date) == month
        ).group_by(Expense.date, Category.id, Category.name, Category.icon, Category.color).all()
        return [(r.date, r.name, r.icon, r.color, float(r.total)) for r in results]


def get_monthly_comparison(user_id: int, year: int, month: int) -> dict:
    """Compare current month with previous month"""
    with get_session() as session:
        # Current month
        current = session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == user_id,
            extract('year', Expense.date) == year,
            extract('month', Expense.date) == month
        ).scalar() or 0.0

        # Previous month
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        previous = session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == user_id,
            extract('year', Expense.date) == prev_year,
            extract('month', Expense.date) == prev_month
        ).scalar() or 0.0

        return {
            "current": float(current),
            "previous": float(previous),
            "difference": float(current) - float(previous),
            "percent_change": ((float(current) - float(previous)) / float(previous) * 100) if previous > 0 else 0
        }


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


def get_budget_by_id(budget_id: int) -> Optional[Budget]:
    with get_session() as session:
        return session.query(Budget).filter(Budget.id == budget_id).first()


def delete_budget(budget_id: int) -> bool:
    with get_session() as session:
        budget = session.query(Budget).filter(Budget.id == budget_id).first()
        if budget:
            session.delete(budget)
            return True
        return False


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