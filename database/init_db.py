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
        users = ["Wife", "Husband"]
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