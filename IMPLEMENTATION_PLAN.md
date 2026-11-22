# Expense Tracker - Implementation Plan

## Project Overview
A personal expense-tracking application for two users (you and your husband) built with **Python + Streamlit**, using **SQLite** for data storage, **Plotly** for interactive charts, and **Gmail SMTP** for automated monthly email reports.

---

## Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Framework** | Streamlit | Rapid development, built-in widgets, great Plotly integration, runs locally |
| **Database** | SQLite | File-based, zero-config, perfect for local personal apps |
| **Charts** | Plotly Express | Interactive, publication-quality, works natively in Streamlit |
| **Email** | smtplib + Gmail SMTP | Free, reliable, uses App Passwords |
| **Scheduling** | APScheduler | Background scheduler for monthly email jobs |
| **Export** | openpyxl / reportlab | Excel and PDF report generation |

---

## Project Structure

```
expense-tracker/
├── app.py                 # Main Streamlit application entry point
├── config.py              # Configuration (DB path, email settings, categories)
├── database/
│   ├── __init__.py
│   ├── models.py          # SQLAlchemy models
│   ├── crud.py            # Database operations
│   └── init_db.py         # Database initialization
├── services/
│   ├── __init__.py
│   ├── expense_service.py # Business logic for expenses
│   ├── report_service.py  # Report generation (Excel/PDF)
│   └── email_service.py   # Gmail SMTP email sending
├── ui/
│   ├── __init__.py
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── 1_📝_Log_Expense.py      # Daily expense entry
│   │   ├── 2_📊_Dashboard.py         # Charts & trends
│   │   ├── 3_📈_Monthly_Summary.py   # Month-end summary
│   │   ├── 4_⚙️_Settings.py          # Categories, budgets, email config
│   │   └── 5_👥_Users.py             # User management
│   └── components.py      # Reusable UI components
├── scheduler/
│   ├── __init__.py
│   └── monthly_job.py     # Monthly email report scheduler
├── utils/
│   ├── __init__.py
│   ├── helpers.py         # Date formatting, currency, etc.
│   └── validators.py      # Input validation
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
├── .gitignore
└── README.md
```

---

## Database Schema (SQLite + SQLAlchemy)

### Tables

**users**
- id (PK), name, email, created_at, is_active

**categories**
- id (PK), name, icon, color, is_default, user_id (FK, nullable for global categories)

**expenses**
- id (PK), user_id (FK), category_id (FK), amount, date, notes, created_at, updated_at

**budgets**
- id (PK), user_id (FK), category_id (FK), month (YYYY-MM), amount, alert_threshold (default 80%)

**email_config** (single row per user)
- id (PK), user_id (FK), smtp_host, smtp_port, email, app_password, recipient_email, is_enabled

---

## Feature Breakdown

### Phase 1: Core Foundation (Week 1)
- [ ] Project setup: virtual env, requirements.txt, config.py
- [ ] Database models & initialization
- [ ] Basic CRUD operations for expenses
- [ ] Streamlit app structure with multi-page layout

### Phase 2: Expense Logging (Week 1-2)
- [ ] Page: "Log Expense" - Date picker, amount input, category dropdown, notes
- [ ] Category management (pre-defined + custom)
- [ ] Input validation & error handling
- [ ] Expense list with edit/delete

### Phase 3: Dashboard & Visualizations (Week 2)
- [ ] Page: "Dashboard" with interactive charts:
  - **Line chart**: Daily spending trend (current month)
  - **Bar chart**: Weekly spending comparison
  - **Pie chart**: Category breakdown (current month)
  - **Heatmap**: Spending by day of week × week of month
- [ ] Date range selector (month, quarter, year, custom)
- [ ] User filter (you / husband / both)

### Phase 4: Monthly Summary (Week 2-3)
- [ ] Page: "Monthly Summary"
- [ ] Total spending, avg daily, top categories
- [ ] Comparison with previous month
- [ ] Budget vs actual (if budgets set)
- [ ] Export to Excel / PDF

### Phase 5: Settings & Multi-User (Week 3)
- [ ] Page: "Settings"
  - Category management (add/edit/delete, icons, colors)
  - Budget setting per category per month
  - Email configuration (Gmail SMTP with App Password)
- [ ] Page: "Users" - Switch between users, add user

### Phase 6: Automated Email Reports (Week 3-4)
- [ ] Monthly report generation (PDF + Excel attachment)
- [ ] Gmail SMTP integration with App Password
- [ ] APScheduler background job (runs 1st of each month)
- [ ] Report includes: summary, charts (as images), category breakdown, budget status

### Phase 7: Polish & Deploy (Week 4)
- [ ] Error handling & logging
- [ ] README with setup instructions
- [ ] .env configuration
- [ ] Test end-to-end flow
- [ ] Optional: Package as executable (PyInstaller)

---

## Key Configuration (`.env`)

```env
# Database
DATABASE_URL=sqlite:///expenses.db

# Gmail SMTP (use App Password, not regular password)
GMAIL_SMTP_HOST=smtp.gmail.com
GMAIL_SMTP_PORT=587
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password
REPORT_RECIPIENT=partner-email@gmail.com

# App
APP_TITLE=Our Expense Tracker
DEFAULT_CURRENCY=₹
TIMEZONE=Asia/Kolkata
```

---

## Pre-defined Categories (Default)

| Category | Icon | Color |
|----------|------|-------|
| 🍔 Food & Dining | 🍔 | #FF6B6B |
| 🚌 Transport | 🚌 | #4ECDC4 |
| 🛒 Groceries | 🛒 | #45B7D1 |
| 🏠 Rent & Utilities | 🏠 | #96CEB4 |
| 🎮 Entertainment | 🎮 | #FFEAA7 |
| 💊 Healthcare | 💊 | #DDA0DD |
| 🛍️ Shopping | 🛍️ | #98D8C8 |
| 📚 Education | 📚 | #F7DC6F |
| 💰 Savings/Investment | 💰 | #82E0AA |
| 🎁 Gifts & Donations | 🎁 | #F8B500 |
| 🔧 Other | 🔧 | #BDC3C7 |

---

## Monthly Email Report Content

**Subject**: `📊 Monthly Expense Report - {Month Year}`

**Body**: HTML email with:
- Summary cards (Total, Avg/Day, Top Category, vs Last Month)
- Embedded charts (as CID images): Category pie, Daily trend line
- Category breakdown table
- Budget status (if configured)
- Attachments: `expenses_{YYYY-MM}.xlsx`, `report_{YYYY-MM}.pdf`

---

## Dependencies (`requirements.txt`)

```txt
# Core
streamlit>=1.35.0
sqlalchemy>=2.0.0
pandas>=2.2.0
plotly>=5.20.0

# Database
alembic>=1.13.0  # for migrations (optional but recommended)

# Email & Scheduling
apscheduler>=3.10.0
python-dotenv>=1.0.0

# Export
openpyxl>=3.1.0
reportlab>=4.0.0
kaleido>=0.1.0  # for static Plotly image export

# Utils
python-dateutil>=2.9.0
```

---

## User Flow

```
1. Launch: streamlit run app.py
2. Select user (sidebar) → "You" or "Husband"
3. Log Expense page:
   - Pick date (defaults to today)
   - Enter amount
   - Select category
   - Add notes (optional)
   - Save → Toast confirmation
4. Dashboard page:
   - View interactive charts
   - Filter by date range, user
   - Hover for details
5. Monthly Summary page:
   - Select month
   - View summary stats
   - Export Excel/PDF
6. Settings page:
   - Manage categories
   - Set monthly budgets
   - Configure Gmail SMTP (test connection)
7. Automatic: 1st of each month → Email sent with report
```

---

## Next Steps

1. **Confirm plan** - Any changes or additions?
2. **Provide Gmail credentials** - You'll need to create an App Password (I'll guide you)
3. **Start implementation** - I'll begin with Phase 1 (project setup + database)

---

## Questions Before Starting

1. **Currency**: Indian Rupees (₹) or another currency?
2. **Date format**: DD/MM/YYYY or MM/DD/YYYY?
3. **First month to track**: Current month (Nov 2026) or earlier?
4. **Run location**: Always on your laptop, or also on husband's? (If both, consider cloud deployment later)
5. **Backup strategy**: Want automatic DB backup to Google Drive/OneDrive?