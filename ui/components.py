import streamlit as st
from datetime import date
from typing import List, Optional, Callable
from database.crud import get_categories, get_user_by_id
from database.models import Category, User
from utils.helpers import format_currency, format_date
from config import config


def render_user_selector(current_user_id: int, on_change: Callable = None):
    """Render user selector in sidebar."""
    users = get_users_for_selector()

    if not users:
        st.sidebar.warning("No users found")
        return None

    user_options = {f"{u.name}": u.id for u in users}
    current_name = next((u.name for u in users if u.id == current_user_id), users[0].name)

    selected_name = st.sidebar.selectbox(
        "👤 Current User",
        options=list(user_options.keys()),
        index=list(user_options.keys()).index(current_name) if current_name in user_options else 0,
        key="user_selector"
    )

    selected_id = user_options[selected_name]

    if on_change and selected_id != current_user_id:
        on_change(selected_id)

    return selected_id


def get_users_for_selector() -> List[User]:
    """Get users for selector (cached)."""
    from database.crud import get_users
    return get_users()


def render_category_selector(user_id: int, selected_category_id: int = None,
                             key: str = "category_selector") -> Optional[int]:
    """Render category dropdown with icons and colors."""
    categories = get_categories(user_id)

    if not categories:
        st.warning("No categories available. Add categories in Settings.")
        return None

    # Create display options with icons
    options = {}
    for cat in categories:
        label = f"{cat.icon} {cat.name}"
        options[label] = cat.id

    # Determine default index
    default_index = 0
    if selected_category_id:
        for i, cat in enumerate(categories):
            if cat.id == selected_category_id:
                default_index = i
                break

    selected_label = st.selectbox(
        "Category",
        options=list(options.keys()),
        index=default_index,
        key=key
    )

    return options[selected_label]


def render_date_picker(label: str = "Date", default: date = None,
                       key: str = "date_picker") -> date:
    """Render date picker with Indian format."""
    if default is None:
        default = date.today()

    return st.date_input(
        label,
        value=default,
        max_value=date.today(),
        format="DD/MM/YYYY",
        key=key
    )


def render_amount_input(label: str = "Amount (₹)", default: float = 0.00,
                        key: str = "amount_input") -> float:
    """Render amount input with validation."""
    amount = st.number_input(
        label,
        min_value=-1000000.0,  # Allow negative for refunds
        max_value=1000000.0,
        value=default,
        step=1.0,
        format="%.2f",
        key=key
    )
    return amount


def render_notes_input(label: str = "Notes (optional)", default: str = "",
                       key: str = "notes_input") -> str:
    """Render notes text area."""
    return st.text_area(
        label,
        value=default,
        max_chars=500,
        height=80,
        key=key
    )


def render_metric_card(title: str, value: str, delta: str = None,
                       delta_color: str = "normal") -> None:
    """Render a metric card."""
    st.metric(label=title, value=value, delta=delta, delta_color=delta_color)


def render_expense_card(expense, user_id: int, on_edit: Callable = None,
                        on_delete: Callable = None) -> None:
    """Render a single expense as a card."""
    from database.crud import get_category_by_id

    cat = get_category_by_id(expense.category_id) if expense.category_id else None
    cat_name = f"{cat.icon} {cat.name}" if cat else "Uncategorized"
    cat_color = cat.color if cat else "#BDC3C7"

    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            st.markdown(f"**{cat_name}**")
            if expense.notes:
                st.caption(expense.notes)

        with col2:
            st.markdown(f"<span style='color: {cat_color}; font-weight: 600;'>{format_currency(expense.amount)}</span>",
                        unsafe_allow_html=True)

        with col3:
            st.caption(format_date(expense.date))

        with col4:
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("✏️", key=f"edit_{expense.id}", help="Edit"):
                    if on_edit:
                        on_edit(expense)
            with btn_col2:
                if st.button("🗑️", key=f"delete_{expense.id}", help="Delete"):
                    if on_delete:
                        on_delete(expense.id)

        st.divider()


def render_empty_state(message: str, icon: str = "📭") -> None:
    """Render empty state message."""
    st.markdown(f"""
    <div style="text-align: center; padding: 3rem; color: #666;">
        <div style="font-size: 3rem;">{icon}</div>
        <p style="font-size: 1.1rem; margin-top: 1rem;">{message}</p>
    </div>
    """, unsafe_allow_html=True)


def render_success_toast(message: str) -> None:
    """Show success toast."""
    st.toast(message, icon="✅")


def render_error_toast(message: str) -> None:
    """Show error toast."""
    st.toast(message, icon="❌")


def render_info_toast(message: str) -> None:
    """Show info toast."""
    st.toast(message, icon="ℹ️")


def render_confirm_dialog(message: str, key: str) -> bool:
    """Render a confirmation dialog. Returns True if confirmed."""
    if f"confirm_{key}" not in st.session_state:
        st.session_state[f"confirm_{key}"] = False

    if not st.session_state[f"confirm_{key}"]:
        if st.button(f"⚠️ {message}", key=f"confirm_btn_{key}", type="secondary"):
            st.session_state[f"confirm_{key}"] = True
            st.rerun()
        return False
    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, confirm", key=f"yes_{key}", type="primary"):
                st.session_state[f"confirm_{key}"] = False
                return True
        with col2:
            if st.button("❌ Cancel", key=f"no_{key}"):
                st.session_state[f"confirm_{key}"] = False
                st.rerun()
        return False


def format_category_display(category: Category) -> str:
    """Format category for display with icon."""
    return f"{category.icon} {category.name}"


def get_category_color(category: Category) -> str:
    """Get category color or default."""
    return category.color if category else "#BDC3C7"