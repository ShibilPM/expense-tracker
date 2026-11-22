import streamlit as st
from datetime import date
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from database.crud import (
    get_expenses, get_category_spending, get_daily_spending,
    get_monthly_total, get_monthly_comparison, get_budgets,
    get_category_by_id, get_user_by_id
)
from utils.helpers import (
    format_currency, format_month_year, get_month_range,
    get_current_month, get_previous_month, get_next_month
)
from ui.components import render_empty_state, render_success_toast, render_error_toast
from config import config


st.set_page_config(page_title="Monthly Summary", page_icon="📈", layout="wide")

# Get current user
user_id = st.session_state.get("current_user_id")
if not user_id:
    st.error("No user selected")
    st.stop()

st.title("📈 Monthly Summary")

# --- Month Navigation ---
col1, col2, col3, col4 = st.columns([1, 2, 1, 2])
current_year, current_month = get_current_month()

with col1:
    if st.button("◀ Previous", use_container_width=True):
        py, pm = get_previous_month(
            st.session_state.get("summary_year", current_year),
            st.session_state.get("summary_month", current_month)
        )
        st.session_state.summary_year = py
        st.session_state.summary_month = pm
        st.rerun()

with col2:
    months = []
    for y in range(current_year - 2, current_year + 1):
        for m in range(1, 13):
            if (y < current_year) or (y == current_year and m <= current_month):
                months.append((y, m))

    month_options = {format_month_year(y, m): (y, m) for y, m in months}
    default_key = format_month_year(
        st.session_state.get("summary_year", current_year),
        st.session_state.get("summary_month", current_month)
    )

    selected = st.selectbox(
        "Select Month",
        options=list(month_options.keys()),
        index=list(month_options.keys()).index(default_key) if default_key in month_options else 0,
        key="summary_month_select"
    )
    year, month = month_options[selected]
    st.session_state.summary_year = year
    st.session_state.summary_month = month

with col3:
    if st.button("Next ▶", use_container_width=True,
                 disabled=(year == current_year and month == current_month)):
        py, pm = get_next_month(year, month)
        st.session_state.summary_year = py
        st.session_state.summary_month = pm
        st.rerun()

with col4:
    st.write("")

# --- Get Data ---
start_date, end_date = get_month_range(year, month)
expenses = get_expenses(user_id=user_id, start_date=start_date, end_date=end_date)

if not expenses:
    render_empty_state(f"No expenses for {format_month_year(year, month)}.", "📈")
    st.stop()

# --- Summary Cards ---
total = sum(e.amount for e in expenses)
comparison = get_monthly_comparison(user_id, year, month)
cat_spending = get_category_spending(user_id, year, month)
budgets = get_budgets(user_id, f"{year}-{month:02d}")

# Budget lookup
budget_dict = {b.category_id: b for b in budgets}

s_col1, s_col2, s_col3, s_col4 = st.columns(4)
with s_col1:
    st.metric("💰 Total Spent", format_currency(total),
              delta=f"{comparison['difference']:,.2f} ₹ vs last month" if comparison['difference'] != 0 else None,
              delta_color="inverse" if comparison['difference'] > 0 else "normal")

with s_col2:
    avg_daily = total / max(1, len(set(e.date for e in expenses)))
    st.metric("📅 Daily Average", format_currency(avg_daily))

with s_col3:
    days_active = len(set(e.date for e in expenses))
    st.metric("📝 Active Days", f"{days_active} / {end_date.day}")

with s_col4:
    # Budget status
    total_budget = sum(b.amount for b in budgets)
    if total_budget > 0:
        pct = (total / total_budget) * 100
        st.metric("🎯 Budget Used", f"{pct:.0f}%",
                  delta=f"{format_currency(total)} / {format_currency(total_budget)}",
                  delta_color="inverse" if pct > 100 else "normal")
    else:
        st.metric("🎯 Budget Used", "No budget set")

st.divider()

# --- Budget vs Actual ---
if budgets:
    st.subheader("🎯 Budget vs Actual")

    budget_data = []
    for b in budgets:
        cat = get_category_by_id(b.category_id)
        actual = next((amt for name, icon, color, amt in cat_spending if cat and name == cat.name), 0)
        pct = (actual / b.amount * 100) if b.amount > 0 else 0
        budget_data.append({
            "Category": f"{cat.icon} {cat.name}" if cat else "Unknown",
            "Budget": b.amount,
            "Actual": actual,
            "Remaining": b.amount - actual,
            "Used %": pct,
            "Status": "🔴 Over" if pct > 100 else ("🟡 Near" if pct > b.alert_threshold * 100 else "🟢 OK"),
            "Color": cat.color if cat else "#BDC3C7"
        })

    df_budget = pd.DataFrame(budget_data)

    # Progress bars
    for _, row in df_budget.iterrows():
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            pct = min(row["Used %"], 150) / 150
            st.progress(pct, text=f"{row['Category']} — {row['Status']}")
        with col2:
            st.markdown(f"**{format_currency(row['Actual'])}** / {format_currency(row['Budget'])}")
        with col3:
            st.caption(f"{row['Used %']:.0f}% used")

st.divider()

# --- Category Breakdown Table ---
st.subheader("📋 Category Breakdown")

if cat_spending:
    df_cat = pd.DataFrame(cat_spending, columns=["Category", "Icon", "Color", "Amount"])
    df_cat["Percentage"] = (df_cat["Amount"] / total * 100).round(1)
    df_cat = df_cat.sort_values("Amount", ascending=False)

    # Add budget info if available
    budget_info = {}
    for b in budgets:
        cat = get_category_by_id(b.category_id)
        if cat:
            budget_info[cat.name] = b.amount

    df_cat["Budget"] = df_cat["Category"].map(budget_info)
    df_cat["Budget"] = df_cat["Budget"].fillna(0)
    df_cat["Budget Used %"] = (df_cat["Amount"] / df_cat["Budget"] * 100).round(1)
    df_cat["Budget Used %"] = df_cat["Budget Used %"].fillna(0)

    st.dataframe(
        df_cat[["Icon", "Category", "Amount", "Percentage", "Budget", "Budget Used %"]].style.format({
            "Amount": "₹{:,.2f}",
            "Percentage": "{:.1f}%",
            "Budget": "₹{:,.2f}",
            "Budget Used %": "{:.1f}%"
        }).apply(lambda row: [f"background-color: {df_cat.loc[row.name, 'Color']}20"] * len(row), axis=1),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Icon": st.column_config.TextColumn("", width="small"),
            "Category": st.column_config.TextColumn("Category", width="medium"),
            "Amount": st.column_config.TextColumn("Spent", width="medium"),
            "Percentage": st.column_config.TextColumn("% of Total", width="small"),
            "Budget": st.column_config.TextColumn("Budget", width="medium"),
            "Budget Used %": st.column_config.TextColumn("Budget Used", width="small"),
        }
    )

st.divider()

# --- Daily Trend Chart ---
st.subheader("📈 Daily Trend")

daily_data = get_daily_spending(user_id, year, month)
if daily_data:
    df_daily = pd.DataFrame(daily_data, columns=["Date", "Amount"])
    df_daily["Date"] = pd.to_datetime(df_daily["Date"])

    # Add cumulative
    df_daily = df_daily.sort_values("Date")
    df_daily["Cumulative"] = df_daily["Amount"].cumsum()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_daily["Date"], y=df_daily["Amount"],
        name="Daily", marker_color="#4ECDC4",
        hovertemplate="<b>%{x|%d %b}</b><br>₹%{y:,.2f}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=df_daily["Date"], y=df_daily["Cumulative"],
        name="Cumulative", mode="lines+markers", line=dict(color="#FF6B6B", width=3),
        yaxis="y2",
        hovertemplate="<b>%{x|%d %b}</b><br>Cumulative: ₹%{y:,.2f}<extra></extra>"
    ))

    fig.update_layout(
        height=400,
        yaxis=dict(title="Daily Amount (₹)", side="left"),
        yaxis2=dict(title="Cumulative (₹)", side="right", overlaying="y", showgrid=False),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=30, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Export Section ---
st.subheader("📤 Export Report")

exp_col1, exp_col2 = st.columns(2)

with exp_col1:
    if st.button("📊 Export to Excel", use_container_width=True, type="primary"):
        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Summary sheet
            summary_df = pd.DataFrame({
                "Metric": ["Month", "Total Spent", "Daily Average", "Active Days",
                          "Top Category", "vs Previous Month", "Budget Total", "Budget Used"],
                "Value": [
                    format_month_year(year, month),
                    format_currency(total),
                    format_currency(avg_daily),
                    f"{days_active} / {end_date.day}",
                    f"{cat_spending[0][1]} {cat_spending[0][0]}" if cat_spending else "—",
                    f"{comparison['difference']:,.2f} ₹ ({comparison['percent_change']:.1f}%)",
                    format_currency(total_budget) if total_budget > 0 else "Not set",
                    f"{(total/total_budget*100):.1f}%" if total_budget > 0 else "—"
                ]
            })
            summary_df.to_excel(writer, sheet_name="Summary", index=False)

            # Category breakdown
            if cat_spending:
                cat_df = pd.DataFrame(cat_spending, columns=["Category", "Icon", "Color", "Amount"])
                cat_df["Percentage"] = (cat_df["Amount"] / total * 100).round(1)
                cat_df["Budget"] = cat_df["Category"].map(budget_info).fillna(0)
                cat_df["Budget Used %"] = (cat_df["Amount"] / cat_df["Budget"].replace(0, pd.NA) * 100).round(1)
                cat_df[["Icon", "Category", "Amount", "Percentage", "Budget", "Budget Used %"]].to_excel(
                    writer, sheet_name="Categories", index=False
                )

            # Daily expenses
            if daily_data:
                daily_df = pd.DataFrame(daily_data, columns=["Date", "Amount"])
                daily_df.to_excel(writer, sheet_name="Daily", index=False)

            # All expenses detail
            expense_rows = []
            for e in sorted(expenses, key=lambda x: x.date):
                cat = get_category_by_id(e.category_id) if e.category_id else None
                expense_rows.append({
                    "Date": e.date.strftime("%d/%m/%Y"),
                    "Category": f"{cat.icon} {cat.name}" if cat else "Uncategorized",
                    "Amount": e.amount,
                    "Notes": e.notes or ""
                })
            pd.DataFrame(expense_rows).to_excel(writer, sheet_name="All Expenses", index=False)

        output.seek(0)
        st.download_button(
            "💾 Download Excel",
            data=output,
            file_name=f"expenses_{year}-{month:02d}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        render_success_toast("Excel report ready!")

with exp_col2:
    if st.button("📄 Export to PDF", use_container_width=True):
        render_info_toast("PDF export coming soon! For now, use Excel export.")

# --- Previous Month Comparison Chart ---
if comparison["previous"] > 0:
    st.divider()
    st.subheader("📊 Month-over-Month Comparison")

    # Get previous month categories
    prev_year, prev_month = get_previous_month(year, month)
    prev_cat_spending = get_category_spending(user_id, prev_year, prev_month)

    # Combine current and previous
    all_categories = set()
    for name, _, _, _ in cat_spending:
        all_categories.add(name)
    for name, _, _, _ in prev_cat_spending:
        all_categories.add(name)

    comparison_data = []
    for cat_name in sorted(all_categories):
        curr = next((amt for n, _, _, amt in cat_spending if n == cat_name), 0)
        prev = next((amt for n, _, _, amt in prev_cat_spending if n == cat_name), 0)
        cat_obj = next((get_category_by_id(cat_id) for cat_id in range(1, 100)
                       if get_category_by_id(cat_id) and get_category_by_id(cat_id).name == cat_name), None)
        icon = cat_obj.icon if cat_obj else "🔧"
        color = cat_obj.color if cat_obj else "#BDC3C7"
        comparison_data.append({
            "Category": f"{icon} {cat_name}",
            "Current": curr,
            "Previous": prev,
            "Change": curr - prev,
            "Change %": ((curr - prev) / prev * 100) if prev > 0 else (100 if curr > 0 else 0),
            "Color": color
        })

    if comparison_data:
        df_comp = pd.DataFrame(comparison_data).sort_values("Current", ascending=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=df_comp["Category"], x=df_comp["Current"],
            name=f"{format_month_year(year, month)}", orientation="h",
            marker_color=df_comp["Color"], opacity=0.8,
            hovertemplate="<b>%{y}</b><br>Current: ₹%{x:,.2f}<extra></extra>"
        ))
        fig.add_trace(go.Bar(
            y=df_comp["Category"], x=df_comp["Previous"],
            name=f"{format_month_year(prev_year, prev_month)}", orientation="h",
            marker_color="#BDC3C7", opacity=0.6,
            hovertemplate="<b>%{y}</b><br>Previous: ₹%{x:,.2f}<extra></extra>"
        ))

        fig.update_layout(
            barmode="group",
            height=max(300, len(df_comp) * 35),
            margin=dict(l=20, r=20, t=30, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Amount (₹)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)