"""
Migration script: moves data from local SQLite (expenses.db) to Supabase PostgreSQL.

Usage:
    1. Set DATABASE_URL in .env to your Supabase PostgreSQL connection string
       e.g., postgresql://postgres:YOUR_PASSWORD@db.eapwnbuecsymtkidzoad.supabase.co:5432/postgres
    2. Run: python migrate_to_postgres.py
    3. Then deploy to Streamlit Cloud with the same DATABASE_URL
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import models after path is set
from database.models import Base, User, Category, Expense, Budget, EmailConfig

# Force psycopg2 usage (psycopg3 may not be installed)
import psycopg2  # noqa: F401 — ensures psycopg2 is available for SQLAlchemy


def migrate():
    source_url = "sqlite:///expenses.db"
    destination_url = os.getenv("DATABASE_URL")
    print(destination_url)

    if not destination_url or destination_url == source_url:
        print("❌ ERROR: DATABASE_URL not set or pointing to SQLite.")
        print("   Set it to your Supabase PostgreSQL URL in .env:")
        print("   postgresql://postgres:YOUR_PASSWORD@db.eapwnbuecsymtkidzoad.supabase.co:5432/postgres")
        sys.exit(1)

    print(f"📥 Reading from SQLite: {source_url}")
    db_host = destination_url.split('@')[1].split('/')[0] if '@' in destination_url else 'unknown'
    print(f"📤 Writing to PostgreSQL: {db_host}...")

    # Create engines
    source_engine = create_engine(source_url, echo=False)
    dest_engine = create_engine(destination_url, echo=False)

    # Inspect source (SQLite)
    source_inspector = inspect(source_engine)
    source_tables = source_inspector.get_table_names()

    print(f"📋 Tables found in SQLite: {source_tables}")

    # Create all tables in destination if they don't exist
    Base.metadata.create_all(dest_engine)
    print("✅ Created/verified tables in PostgreSQL")

    # Get session makers
    SourceSession = sessionmaker(bind=source_engine)
    DestSession = sessionmaker(bind=dest_engine)

    # Migrate data table by table
    with SourceSession() as source_session:
        with DestSession() as dest_session:

            # 1. Migrate Users
            print("\n👥 Migrating Users...")
            for user in source_session.query(User).all():
                existing = dest_session.query(User).filter_by(id=user.id).first()
                if not existing:
                    dest_user = User(
                        id=user.id,
                        name=user.name,
                        email=user.email,
                        created_at=user.created_at,
                        is_active=user.is_active
                    )
                    dest_session.add(dest_user)
                    print(f"   Added user: {user.name}")

            dest_session.commit()

            # 2. Migrate Categories
            print("\n📂 Migrating Categories...")
            for cat in source_session.query(Category).all():
                existing = dest_session.query(Category).filter_by(id=cat.id).first()
                if not existing:
                    dest_cat = Category(
                        id=cat.id,
                        name=cat.name,
                        icon=cat.icon,
                        color=cat.color,
                        is_default=cat.is_default,
                        user_id=cat.user_id
                    )
                    dest_session.add(dest_cat)
                    print(f"   Added category: {cat.name}")

            dest_session.commit()

            # 3. Migrate Expenses
            print("\n💰 Migrating Expenses...")
            for exp in source_session.query(Expense).all():
                existing = dest_session.query(Expense).filter_by(id=exp.id).first()
                if not existing:
                    dest_exp = Expense(
                        id=exp.id,
                        user_id=exp.user_id,
                        category_id=exp.category_id,
                        amount=exp.amount,
                        date=exp.date,
                        notes=exp.notes,
                        created_at=exp.created_at,
                        updated_at=exp.updated_at
                    )
                    dest_session.add(dest_exp)
                    print(f"   Added expense: {exp.amount} - {exp.date}")

            dest_session.commit()

            # 4. Migrate Budgets
            print("\n📊 Migrating Budgets...")
            for bud in source_session.query(Budget).all():
                existing = dest_session.query(Budget).filter_by(id=bud.id).first()
                if not existing:
                    dest_bud = Budget(
                        id=bud.id,
                        user_id=bud.user_id,
                        category_id=bud.category_id,
                        month=bud.month,
                        amount=bud.amount,
                        alert_threshold=bud.alert_threshold
                    )
                    dest_session.add(dest_bud)
                    print(f"   Added budget: {bud.month} - cat {bud.category_id}")

            dest_session.commit()

            # 5. Migrate Email Config
            print("\n📧 Migrating Email Config...")
            for ec in source_session.query(EmailConfig).all():
                existing = dest_session.query(EmailConfig).filter_by(id=ec.id).first()
                if not existing:
                    dest_ec = EmailConfig(
                        id=ec.id,
                        user_id=ec.user_id,
                        smtp_host=ec.smtp_host,
                        smtp_port=ec.smtp_port,
                        email=ec.email,
                        app_password=ec.app_password,
                        recipient_email=ec.recipient_email,
                        is_enabled=ec.is_enabled,
                        last_sent=ec.last_sent
                    )
                    dest_session.add(dest_ec)
                    print(f"   Added email config for user {ec.user_id}")

            dest_session.commit()

    print("\n🎉 Migration completed successfully!")
    print(f"📍 Your data is now in PostgreSQL")
    print("🔄 You can now deploy to Streamlit Cloud with the same DATABASE_URL")
    print("   and your data will persist across deployments.")


if __name__ == "__main__":
    migrate()