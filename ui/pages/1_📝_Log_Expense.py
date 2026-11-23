import streamlit as st
from datetime import date
from database.crud import (
    create_expense, get_expenses, update_expense, delete_expense,
    get_categories, get_user_by_name
)
from ui.components import (
    render_category_selector, render_date_picker, render_amount_input,
    render_notes_input, render_success_toast, render_error_toast,
    render_expense_card, render_empty_state, render_confirm_dialog
)
from utils.validators import validate_expense_input


# Page config
st.set_page_config(page_title="Log Expense", page_icon="📝", layout="wide")

# Get current user
user_id = st.session_state.get("current_user_id")
if not user_id:
    st.error("No user selected")
    st.stop()

st.title("📝 Log Expense")

# --- Add Expense Form ---
with st.container(border=True):
    st.subheader("➕ Add New Expense")

    col1, col2 = st.columns(2)

    with col1:
        expense_date = render_date_picker("Date", key="new_expense_date")
        category_id = render_category_selector(user_id, key="new_expense_category")

    with col2:
        amount = render_amount_input("Amount (₹)", key="new_expense_amount")
        notes = render_notes_input("Notes (optional)", key="new_expense_notes")

    # Submit button
    if st.button("💾 Save Expense", type="primary", use_container_width=True):
        is_valid, error_msg = validate_expense_input(
            str(amount), expense_date, category_id, user_id
        )
        if is_valid:
            create_expense(user_id, category_id, amount, expense_date, notes or None)
            render_success_toast("Expense saved successfully!")
            st.rerun()
        else:
            render_error_toast(error_msg)

st.divider()

# --- Expense List ---
st.subheader("📋 Your Expenses")

# Filter options
col1, col2, col3 = st.columns(3)
with col1:
    filter_month = st.selectbox(
        "Month",
        options=[(date.today().year, date.today().month)] +
                [(date.today().year, m) for m in range(1, 13) if m != date.today().month] +
                [(date.today().year - 1, m) for m in range(1, 13)],
        format_func=lambda x: f"{x[0]}-{x[1]:02d}",
        key="expense_filter_month"
    )

with col2:
    from database.crud import get_categories
    all_cats = get_categories(user_id)
    cat_options = {f"{c.icon} {c.name}": c.id for c in all_cats}
    cat_options["All Categories"] = None
    filter_category = st.selectbox(
        "Category",
        options=list(cat_options.keys()),
        index=0,
        key="expense_filter_category"
    )

with col3:
    show_all = st.checkbox("Show all months", key="expense_show_all")

# Get expenses
if show_all:
    expenses = get_expenses(user_id=user_id)
else:
    year, month = filter_month
    from utils.helpers import get_month_range
    start_date, end_date = get_month_range(year, month)
    cat_id = cat_options[filter_category]
    expenses = get_expenses(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        category_id=cat_id
    )

# Display expenses
if expenses:
    # Summary
    total = sum(e.amount for e in expenses)
    st.markdown(f"**Total: {len(expenses)} expenses • {total:,.2f} ₹**")

    for expense in expenses:
        def make_edit_handler(exp):
            def handler(_=None):  # Accept arg from button on_click
                st.session_state[f"editing_{exp.id}"] = True
                st.session_state[f"edit_amount_{exp.id}"] = exp.amount
                st.session_state[f"edit_date_{exp.id}"] = exp.date
                st.session_state[f"edit_cat_{exp.id}"] = exp.category_id
                st.session_state[f"edit_notes_{exp.id}"] = exp.notes or ""
            return handler

        def make_delete_handler(exp_id):
            def handler(_=None):  # Accept arg from button on_click
                if render_confirm_dialog(f"Delete this expense?", f"delete_exp_{exp_id}"):
                    delete_expense(exp_id)
                    render_success_toast("Expense deleted!")
                    st.rerun()
            return handler

        # Check if editing
        if st.session_state.get(f"editing_{expense.id}", False):
            with st.container(border=True):
                st.markdown("**✏️ Edit Expense**")
                e_col1, e_col2 = st.columns(2)
                with e_col1:
                    edit_date = render_date_picker("Date", expense.date, key=f"edit_date_{expense.id}")
                    edit_cat = render_category_selector(user_id, expense.category_id, key=f"edit_cat_{expense.id}")
                with e_col2:
                    edit_amount = render_amount_input("Amount", expense.amount, key=f"edit_amount_{expense.id}")
                    edit_notes = render_notes_input("Notes", expense.notes or "", key=f"edit_notes_{expense.id}")

                e_btn1, e_btn2 = st.columns(2)
                with e_btn1:
                    if st.button("💾 Save", key=f"save_edit_{expense.id}", type="primary"):
                        is_valid, err = validate_expense_input(
                            str(edit_amount), edit_date, edit_cat, user_id
                        )
                        if is_valid:
                            update_expense(expense.id, amount=edit_amount, date=edit_date,
                                          category_id=edit_cat, notes=edit_notes or None)
                            st.session_state[f"editing_{expense.id}"] = False
                            render_success_toast("Expense updated!")
                            st.rerun()
                        else:
                            render_error_toast(err)
                with e_btn2:
                    if st.button("❌ Cancel", key=f"cancel_edit_{expense.id}"):
                        st.session_state[f"editing_{expense.id}"] = False
                        st.rerun()
        else:
            render_expense_card(
                expense, user_id,
                on_edit=make_edit_handler(expense),
                on_delete=make_delete_handler(expense.id)
            )
else:
    render_empty_state("No expenses found for this period. Add your first expense above!")