from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from config import config, DEFAULT_CATEGORIES
from database.models import Base, User, Category, Expense


def init_database():
    """Create database tables and seed default data — idempotent, safe to run multiple times."""
    engine = create_engine(config.DATABASE_URL, echo=False)

    # Create all tables (idempotent — no-op if tables exist)
    Base.metadata.create_all(engine)

    # Reset sequences to prevent "duplicate key" errors after migration from SQLite
    # This ensures auto-increment IDs start after existing data
    with engine.connect() as conn:
        # Get all table names
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        for table in tables:
            # Check if table has an 'id' column (primary key)
            has_id = any(col['name'] == 'id' for col in inspector.get_columns(table))
            if has_id:
                try:
                    # Reset the sequence for the id column
                    seq_name = f"{table}_id_seq"
                    conn.execute(text(f"SELECT setval('{seq_name}', 1, (SELECT MAX(id) FROM {table}) OR 1)"))
                except Exception:
                    # Some tables may not have sequences; ignore if it fails
                    pass

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Create default users if not exist (check by name)
        users = ["Wife", "Husband"]
        for name in users:
            if not session.query(User).filter_by(name=name).first():
                user = User(name=name)
                session.add(user)
        session.commit()

        # Seed global default categories if not exist (check by name + user_id=None)
        for name, icon, color in DEFAULT_CATEGORIES:
            if not session.query(Category).filter_by(name=name, user_id=None).first():
                cat = Category(name=name, icon=icon, color=color, is_default=True, user_id=None)
                session.add(cat)
        session.commit()

        # Seed default budgets for existing users/categories (idempotent)
        for user in session.query(User).all():
            for name, icon, color in DEFAULT_CATEGORIES:
                cat = session.query(Category).filter_by(name=name, user_id=user.id).first()
                if cat:
                    existing = session.query(Budget).filter_by(
                        user_id=user.id,
                        category_id=cat.id,
                        month=date.today().strftime("%Y-%m")
                    ).first()
                    if not existing:
                        budget = Budget(
                            user_id=user.id,
                            category_id=cat.id,
                            month=date.today().strftime("%Y-%m"),
                            amount=0.0,
                            alert_threshold=0.8
                        )
                        session.add(budget)
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