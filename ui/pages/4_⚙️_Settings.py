import streamlit as st
from datetime import date
from database.crud import (
    get_categories, create_category, update_category, delete_category,
    get_budgets, set_budget, delete_budget, get_category_by_id,
    get_email_config, upsert_email_config
)
from utils.validators import validate_category_input, validate_budget_input, validate_email_config
from ui.components import (
    render_category_selector, render_success_toast, render_error_toast,
    render_info_toast, render_confirm_dialog, render_empty_state
)
from config import DEFAULT_CATEGORIES


st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

user_id = st.session_state.get("current_user_id")
if not user_id:
    st.error("No user selected")
    st.stop()

st.title("⚙️ Settings")

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["📂 Categories", "🎯 Budgets", "📧 Email Reports", "🔧 App Settings"])

# ========== TAB 1: CATEGORIES ==========
with tab1:
    st.subheader("📂 Manage Categories")

    # Add new category
    with st.expander("➕ Add New Category", expanded=False):
        with st.form("add_category_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                new_name = st.text_input("Category Name", placeholder="e.g., Dining Out")
            with col2:
                new_icon = st.text_input("Icon (emoji)", placeholder="🍽️", max_chars=2)
            with col3:
                new_color = st.color_picker("Color", value="#4ECDC4")

            if st.form_submit_button("Add Category", type="primary"):
                is_valid, err = validate_category_input(new_name, new_icon, new_color)
                if is_valid:
                    create_category(new_name.strip(), new_icon.strip() or "🔧", new_color, user_id)
                    render_success_toast(f"Category '{new_name}' added!")
                    st.rerun()
                else:
                    render_error_toast(err)

    st.divider()

    # List categories
    categories = get_categories(user_id)

    if categories:
        st.markdown("**Your Categories** (global categories shown with 🌐)")
        for cat in categories:
            is_global = cat.user_id is None
            label = f"{'🌐 ' if is_global else ''}{cat.icon} {cat.name}"

            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                with c1:
                    st.markdown(f"**{label}**")
                    st.caption(f"Color: {cat.color}" + (" • Global" if is_global else " • Personal"))
                with c2:
                    # Color preview
                    st.markdown(
                        f"<div style='width: 30px; height: 30px; background: {cat.color}; "
                        f"border-radius: 4px; border: 1px solid #ddd;'></div>",
                        unsafe_allow_html=True
                    )
                with c3:
                    if not is_global:
                        if st.button("✏️ Edit", key=f"edit_cat_{cat.id}"):
                            st.session_state[f"editing_cat_{cat.id}"] = True
                            st.rerun()
                with c4:
                    if not is_global and not cat.is_default:
                        if st.button("🗑️ Delete", key=f"del_cat_{cat.id}"):
                            if render_confirm_dialog(f"Delete '{cat.name}'?", f"del_cat_{cat.id}"):
                                delete_category(cat.id)
                                render_success_toast("Category deleted!")
                                st.rerun()
                    elif cat.is_default:
                        st.caption("🔒 Default")

                # Edit form
                if st.session_state.get(f"editing_cat_{cat.id}", False):
                    with st.form(f"edit_cat_form_{cat.id}"):
                        e_col1, e_col2, e_col3 = st.columns(3)
                        with e_col1:
                            edit_name = st.text_input("Name", value=cat.name)
                        with e_col2:
                            edit_icon = st.text_input("Icon", value=cat.icon, max_chars=2)
                        with e_col3:
                            edit_color = st.color_picker("Color", value=cat.color)

                        e_btn1, e_btn2 = st.columns(2)
                        with e_btn1:
                            if st.form_submit_button("💾 Save", type="primary"):
                                is_valid, err = validate_category_input(edit_name, edit_icon, edit_color)
                                if is_valid:
                                    update_category(cat.id, name=edit_name.strip(),
                                                    icon=edit_icon.strip(), color=edit_color)
                                    st.session_state[f"editing_cat_{cat.id}"] = False
                                    render_success_toast("Category updated!")
                                    st.rerun()
                                else:
                                    render_error_toast(err)
                        with e_btn2:
                            if st.form_submit_button("❌ Cancel"):
                                st.session_state[f"editing_cat_{cat.id}"] = False
                                st.rerun()
    else:
        render_empty_state("No categories yet. Add your first category above!")

# ========== TAB 2: BUDGETS ==========
with tab2:
    st.subheader("🎯 Monthly Budgets")

    # Month selector
    from utils.helpers import get_current_month, format_month_year, get_previous_month, get_next_month
    current_year, current_month = get_current_month()

    # Initialize session state for budget month
    if "budget_year" not in st.session_state:
        st.session_state.budget_year = current_year
    if "budget_month" not in st.session_state:
        st.session_state.budget_month = current_month

    b_col1, b_col2, b_col3, b_col4 = st.columns([1, 2, 1, 4])
    with b_col1:
        if st.button("◀", key="budget_prev", use_container_width=True):
            py, pm = get_previous_month(st.session_state.budget_year, st.session_state.budget_month)
            st.session_state.budget_year, st.session_state.budget_month = py, pm
            st.rerun()
    with b_col2:
        month_str = format_month_year(st.session_state.budget_year, st.session_state.budget_month)
        st.markdown(f"### {month_str}")
    with b_col3:
        if st.button("▶", key="budget_next", use_container_width=True,
                     disabled=(st.session_state.budget_year == current_year and
                              st.session_state.budget_month == current_month)):
            py, pm = get_next_month(st.session_state.budget_year, st.session_state.budget_month)
            st.session_state.budget_year, st.session_state.budget_month = py, pm
            st.rerun()

    month_key = f"{st.session_state.budget_year}-{st.session_state.budget_month:02d}"

    # Add budget
    with st.expander("➕ Set Budget for Category", expanded=False):
        with st.form("add_budget_form"):
            categories = get_categories(user_id)
            if categories:
                cat_options = {f"{c.icon} {c.name}": c.id for c in categories}
                selected_cat_label = st.selectbox("Category", options=list(cat_options.keys()))
                selected_cat_id = cat_options[selected_cat_label]

                b_col1, b_col2 = st.columns(2)
                with b_col1:
                    budget_amount = st.number_input("Budget Amount (₹)", min_value=1.0, step=100.0, format="%.2f")
                with b_col2:
                    alert_threshold = st.slider("Alert Threshold (%)", 50, 100, 80,
                                                help="Get warned when spending reaches this % of budget")

                if st.form_submit_button("Set Budget", type="primary"):
                    is_valid, err = validate_budget_input(str(budget_amount), selected_cat_id, month_key)
                    if is_valid:
                        set_budget(user_id, selected_cat_id, month_key, budget_amount, alert_threshold / 100)
                        render_success_toast(f"Budget set for {selected_cat_label}!")
                        st.rerun()
                    else:
                        render_error_toast(err)
            else:
                st.warning("No categories available. Add categories first.")

    st.divider()

    # Show existing budgets
    budgets = get_budgets(user_id, month_key)

    if budgets:
        st.markdown(f"**Budgets for {month_str}**")
        for b in budgets:
            cat = get_category_by_id(b.category_id)
            cat_label = f"{cat.icon} {cat.name}" if cat else "Unknown"

            with st.container(border=True):
                b1, b2, b3, b4 = st.columns([3, 1, 1, 1])
                with b1:
                    st.markdown(f"**{cat_label}**")
                with b2:
                    st.markdown(f"**{b.amount:,.2f} ₹**")
                with b3:
                    st.caption(f"Alert at {b.alert_threshold*100:.0f}%")
                with b4:
                    if st.button("🗑️", key=f"del_budget_{b.id}"):
                        if render_confirm_dialog(f"Delete budget for {cat_label}?", f"del_budget_{b.id}"):
                            delete_budget(b.id)
                            render_success_toast("Budget deleted!")
                            st.rerun()
    else:
        render_empty_state(f"No budgets set for {month_str}. Set budgets above to track spending!")

# ========== TAB 3: EMAIL REPORTS ==========
with tab3:
    st.subheader("📧 Monthly Email Reports")

    st.info("""
    **Setup Gmail App Password:**
    1. Go to [Google Account Security](https://myaccount.google.com/security)
    2. Enable **2-Step Verification** if not already enabled
    3. Search for "App passwords" and create one for "Mail"
    4. Use the 16-character password below (no spaces)
    """)

    email_config = get_email_config(user_id)

    with st.form("email_config_form"):
        st.markdown("**SMTP Settings**")
        e_col1, e_col2 = st.columns(2)
        with e_col1:
            smtp_host = st.text_input("SMTP Host", value=email_config.smtp_host if email_config else "smtp.gmail.com")
            smtp_port = st.number_input("SMTP Port", value=email_config.smtp_port if email_config else 587, min_value=1, max_value=65535)
        with e_col2:
            sender_email = st.text_input("Your Gmail Address", value=email_config.email if email_config else "",
                                         placeholder="you@gmail.com")
            app_password = st.text_input("App Password (16 chars)", type="password",
                                         value=email_config.app_password if email_config else "",
                                         placeholder="xxxx xxxx xxxx xxxx")

        st.markdown("**Report Recipient**")
        recipient_email = st.text_input("Send Report To", value=email_config.recipient_email if email_config else "",
                                        placeholder="partner@gmail.com")

        is_enabled = st.checkbox("Enable Monthly Reports",
                                 value=email_config.is_enabled if email_config else False,
                                 help="Automatically send report on 1st of each month")

        if st.form_submit_button("💾 Save Email Config", type="primary"):
            is_valid, err = validate_email_config(smtp_host, str(smtp_port),
                                                  sender_email, app_password, recipient_email)
            if is_valid:
                upsert_email_config(user_id, smtp_host, smtp_port,
                                    sender_email, app_password.replace(" ", ""),
                                    recipient_email, is_enabled)
                render_success_toast("Email configuration saved!")
                st.rerun()
            else:
                render_error_toast(err)

    if email_config and email_config.is_enabled:
        st.divider()
        st.success("✅ Monthly reports are **ENABLED**")
        st.caption(f"Reports will be sent to {email_config.recipient_email} on the 1st of each month.")

        if st.button("📤 Send Test Report Now", type="secondary"):
            render_info_toast("Test sending coming in Phase 6!")

# ========== TAB 4: APP SETTINGS ==========
with tab4:
    st.subheader("🔧 App Settings")

    st.markdown("**Display Preferences**")

    # Currency
    from config import config
    currency = st.selectbox("Default Currency", ["₹", "$", "€", "£", "¥"],
                            index=["₹", "$", "€", "£", "¥"].index(config.DEFAULT_CURRENCY))

    # Date format
    date_fmt = st.selectbox("Date Format", ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"],
                            index=["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"].index(config.DATE_FORMAT))

    st.divider()

    st.markdown("**Data Management**")

    if st.button("📥 Export All Data (Excel)", use_container_width=True):
        render_info_toast("Full data export coming in Phase 6!")

    if st.button("🗑️ Clear All My Data", type="secondary", use_container_width=True):
        if render_confirm_dialog("⚠️ This will delete ALL your expenses, budgets, and categories. Cannot be undone!", "clear_all_data"):
            render_error_toast("Data clearing not implemented yet - safety first!")

    st.divider()

    st.markdown("**About**")
    st.caption("Our Expense Tracker v1.0")
    st.caption("Built with Streamlit + SQLite + Plotly")