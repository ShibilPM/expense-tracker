import streamlit as st
from datetime import date, timedelta
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from database.crud import (
    get_expenses, get_category_spending, get_daily_spending,
    get_weekly_spending, get_monthly_total, get_monthly_comparison,
    get_expenses_by_category_and_date, get_users
)
from utils.helpers import (
    format_currency, format_month_year, get_month_range,
    get_current_month, calculate_percentage_change
)
from ui.components import render_category_selector, render_empty_state


st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# Get current user
user_id = st.session_state.get("current_user_id")
if not user_id:
    st.error("No user selected")
    st.stop()

st.title("📊 Dashboard")

# --- Month Selector ---
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    current_year, current_month = get_current_month()
    months = []
    for y in range(current_year - 1, current_year + 1):
        for m in range(1, 13):
            if (y < current_year) or (y == current_year and m <= current_month):
                months.append((y, m))

    month_options = {format_month_year(y, m): (y, m) for y, m in months}
    default_key = format_month_year(current_year, current_month)

    selected_month_str = st.selectbox(
        "Select Month",
        options=list(month_options.keys()),
        index=list(month_options.keys()).index(default_key) if default_key in month_options else 0,
        key="dashboard_month"
    )

    selected_year, selected_month = month_options[selected_month_str]

with col2:
    # User filter for comparison
    users = get_users()
    if len(users) > 1:
        user_options = {u.name: u.id for u in users}
        user_options["Both"] = "both"
        selected_user_filter = st.selectbox(
            "View",
            options=list(user_options.keys()),
            index=0,
            key="dashboard_user_filter"
        )
        filter_user_id = user_options[selected_user_filter]
    else:
        filter_user_id = user_id

with col3:
    st.write("")  # Spacer
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

# Get data
if filter_user_id == "both":
    # For "both", we'll show combined data
    expenses = get_expenses(start_date=get_month_range(selected_year, selected_month)[0],
                           end_date=get_month_range(selected_year, selected_month)[1])
else:
    expenses = get_expenses(user_id=filter_user_id,
                           start_date=get_month_range(selected_year, selected_month)[0],
                           end_date=get_month_range(selected_year, selected_month)[1])

if not expenses:
    render_empty_state("No expenses for this month. Go to 'Log Expense' to add some!", "📊")
    st.stop()

# --- Summary Metrics ---
total = sum(e.amount for e in expenses)
avg_daily = total / max(1, len(set(e.date for e in expenses)))
comparison = get_monthly_comparison(filter_user_id if filter_user_id != "both" else user_id,
                                    selected_year, selected_month) if filter_user_id != "both" else {"current": total, "previous": 0, "difference": 0, "percent_change": 0}

m_col1, m_col2, m_col3, m_col4 = st.columns(4)

with m_col1:
    st.metric("💰 Total This Month", format_currency(total),
              delta=f"{comparison['difference']:,.2f} ₹" if comparison['difference'] != 0 else None,
              delta_color="inverse" if comparison['difference'] > 0 else "normal")

with m_col2:
    st.metric("📅 Avg / Day", format_currency(avg_daily))

with m_col3:
    unique_days = len(set(e.date for e in expenses))
    st.metric("📝 Days with Expenses", f"{unique_days} / {get_month_range(selected_year, selected_month)[1].day}")

with m_col4:
    # Top category
    cat_spending = get_category_spending(filter_user_id if filter_user_id != "both" else user_id,
                                         selected_year, selected_month)
    if cat_spending:
        top_cat = max(cat_spending, key=lambda x: x[3])
        st.metric("🏆 Top Category", f"{top_cat[1]} {top_cat[0]}",
                  delta=format_currency(top_cat[3]))
    else:
        st.metric("🏆 Top Category", "—")

st.divider()

# --- Charts Row 1: Daily Trend + Category Breakdown ---
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("📈 Daily Spending Trend")

    daily_data = get_daily_spending(filter_user_id if filter_user_id != "both" else user_id,
                                    selected_year, selected_month)
    if daily_data:
        df_daily = pd.DataFrame(daily_data, columns=["Date", "Amount"])
        df_daily["Date"] = pd.to_datetime(df_daily["Date"])

        fig = px.line(df_daily, x="Date", y="Amount",
                      markers=True,
                      labels={"Amount": "Amount (₹)", "Date": "Date"},
                      line_shape="spline")
        fig.update_traces(line_color="#4ECDC4", line_width=3, marker_size=8,
                          hovertemplate="<b>%{x|%d %b}</b><br>₹%{y:,.2f}<extra></extra>")
        fig.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=30, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.1)"),
            yaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.1)"),
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        render_empty_state("No daily data", "📈")

with chart_col2:
    st.subheader("🥧 Category Breakdown")

    if cat_spending:
        df_cat = pd.DataFrame(cat_spending, columns=["Category", "Icon", "Color", "Amount"])
        df_cat["Label"] = df_cat["Icon"] + " " + df_cat["Category"]

        fig = px.pie(df_cat, values="Amount", names="Label",
                     color_discrete_sequence=df_cat["Color"].tolist(),
                     hole=0.4)
        fig.update_traces(textposition="inside", textinfo="percent+label",
                          hovertemplate="<b>%{label}</b><br>₹%{value:,.2f} (%{percent})<extra></extra>")
        fig.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=30, b=20),
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        render_empty_state("No category data", "🥧")

st.divider()

# --- Charts Row 2: Weekly Comparison + Heatmap ---
chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    st.subheader("📊 Weekly Spending")

    weekly_data = get_weekly_spending(filter_user_id if filter_user_id != "both" else user_id,
                                      selected_year, selected_month)
    if weekly_data:
        df_weekly = pd.DataFrame(weekly_data, columns=["Week", "Amount"])
        df_weekly["Week Label"] = "Week " + df_weekly["Week"].astype(str)

        fig = px.bar(df_weekly, x="Week Label", y="Amount",
                     color="Amount", color_continuous_scale="Teal",
                     labels={"Amount": "Amount (₹)", "Week Label": "Week"})
        fig.update_traces(hovertemplate="<b>%{x}</b><br>₹%{y:,.2f}<extra></extra>")
        fig.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=30, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(128,128,128,0.1)"),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        render_empty_state("No weekly data", "📊")

with chart_col4:
    st.subheader("🔥 Spending Heatmap")

    heatmap_data = get_expenses_by_category_and_date(
        filter_user_id if filter_user_id != "both" else user_id,
        selected_year, selected_month
    )

    if heatmap_data:
        # Create pivot table for heatmap
        df_hm = pd.DataFrame(heatmap_data, columns=["Date", "Category", "Icon", "Color", "Amount"])
        df_hm["Date"] = pd.to_datetime(df_hm["Date"])
        df_hm["Day"] = df_hm["Date"].dt.day
        df_hm["Weekday"] = df_hm["Date"].dt.weekday  # 0=Monday
        df_hm["WeekOfMonth"] = df_hm["Day"].apply(lambda d: (d - 1) // 7)

        # Pivot for heatmap
        pivot = df_hm.pivot_table(index="WeekOfMonth", columns="Weekday",
                                  values="Amount", aggfunc="sum", fill_value=0)

        # Ensure all weekdays present
        for wd in range(7):
            if wd not in pivot.columns:
                pivot[wd] = 0
        pivot = pivot.reindex(sorted(pivot.columns), axis=1)

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            y=[f"Week {i+1}" for i in pivot.index],
            colorscale="Teal",
            showscale=False,
            hovertemplate="<b>%{y} - %{x}</b><br>₹%{z:,.2f}<extra></extra>",
            text=pivot.values,
            texttemplate="₹%{z:,.0f}",
            textfont={"size": 10}
        ))
        fig.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(side="top")
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        render_empty_state("No heatmap data", "🔥")

st.divider()

# --- Category Table ---
st.subheader("📋 Category Details")

if cat_spending:
    df_table = pd.DataFrame(cat_spending, columns=["Category", "Icon", "Color", "Amount"])
    df_table["Percentage"] = (df_table["Amount"] / total * 100).round(1)
    df_table = df_table.sort_values("Amount", ascending=False)

    # Style the dataframe
    def color_row(row):
        Color = df_table.loc[row.name, "Color"]
        return [f"background-color: {df_table.loc[row.name, 'Color']}20"] * len(row)

    st.dataframe(
        df_table[["Icon", "Category", "Amount", "Percentage"]].style.format({
            "Amount": "₹{:,.2f}",
            "Percentage": "{:.1f}%"
        }).apply(color_row, axis=1),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Icon": st.column_config.TextColumn("Icon", width="small"),
            "Category": st.column_config.TextColumn("Category", width="medium"),
            "Amount": st.column_config.TextColumn("Amount", width="medium"),
            "Percentage": st.column_config.TextColumn("% of Total", width="small"),
        }
    )