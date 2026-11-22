# 💰 Our Expense Tracker

A personal expense tracking application for couples, built with **Streamlit**, **SQLite**, and **Plotly**.

## Features

- 📝 **Daily Expense Logging** — Date, amount, category, notes with full CRUD
- 📊 **Interactive Dashboard** — Daily trends, category breakdown, weekly comparison, spending heatmap
- 📈 **Monthly Summary** — Detailed reports with budget vs actual, month-over-month comparison
- 🎯 **Budget Tracking** — Set monthly budgets per category with alert thresholds
- 👥 **Multi-User** — Separate tracking for you and your husband
- 📂 **Custom Categories** — Add/edit/delete categories with icons and colors
- 📧 **Email Reports** — Monthly automated reports via Gmail SMTP (Phase 6)
- 📤 **Excel Export** — Download monthly reports as formatted Excel files

## Quick Start

### 1. Create Virtual Environment
```powershell
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Configure Environment
```powershell
copy .env.example .env
```
Edit `.env` with your settings:
- **Gmail SMTP**: Create an [App Password](https://myaccount.google.com/apppasswords) (requires 2FA)
- **REPORT_RECIPIENT**: Email to receive monthly reports

### 4. Initialize Database
```powershell
python database/init_db.py
```

### 5. Run the App
```powershell
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Project Structure

```
expense-tracker/
├── app.py                 # Main entry point
├── config.py              # Configuration & default categories
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── .gitignore
├── database/
│   ├── models.py          # SQLAlchemy models
│   ├── crud.py            # Database operations
│   └── init_db.py         # Database initialization
├── services/              # Business logic (Phase 6+)
├── ui/
│   ├── components.py      # Reusable UI components
│   └── pages/             # Streamlit pages
│       ├── 1_📝_Log_Expense.py
│       ├── 2_📊_Dashboard.py
│       ├── 3_📈_Monthly_Summary.py
│       ├── 4_⚙️_Settings.py
│       └── 5_👥_Users.py
├── utils/
│   ├── helpers.py         # Date/currency formatting
│   └── validators.py      # Input validation
└── scheduler/
    └── monthly_job.py     # Background email scheduler (Phase 6)
```

## Default Categories

| Category | Icon | Color |
|----------|------|-------|
| Food & Dining | 🍔 | #FF6B6B |
| Transport | 🚌 | #4ECDC4 |
| Groceries | 🛒 | #45B7D1 |
| Rent & Utilities | 🏠 | #96CEB4 |
| Entertainment | 🎮 | #FFEAA7 |
| Healthcare | 💊 | #DDA0DD |
| Shopping | 🛍️ | #98D8C8 |
| Education | 📚 | #F7DC6F |
| Savings/Investment | 💰 | #82E0AA |
| Gifts & Donations | 🎁 | #F8B500 |
| Other | 🔧 | #BDC3C7 |

## Gmail App Password Setup

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification**
3. Search **"App passwords"**
4. Create new app password for **"Mail"**
5. Copy the 16-character password (no spaces) to `.env`

## Usage Tips

- **Switch users** via sidebar dropdown
- **Edit/Delete expenses** by clicking icons in the expense list
- **Set budgets** in Settings → Budgets for each month
- **Export to Excel** from Monthly Summary page
- **Custom categories** persist per user; global categories (🌐) are shared

## Roadmap

- [x] Phase 1: Project setup, database, basic UI structure
- [x] Phase 2: Expense logging (CRUD)
- [x] Phase 3: Dashboard with charts
- [x] Phase 4: Monthly summary with export
- [x] Phase 5: Settings, categories, budgets, users
- [ ] Phase 6: Email reports & scheduler
- [ ] Phase 7: PDF export, data backup, packaging

## License

Personal use only.