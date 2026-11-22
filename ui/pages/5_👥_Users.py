import streamlit as st
from database.crud import get_users, create_user, update_user, get_user_by_name
from ui.components import render_success_toast, render_error_toast, render_confirm_dialog, render_empty_state


st.set_page_config(page_title="Users", page_icon="👥", layout="wide")

st.title("👥 User Management")

# Current user
current_user_id = st.session_state.get("current_user_id")

# --- Add User ---
with st.expander("➕ Add New User", expanded=False):
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("Name", placeholder="e.g., Mom, Dad, Kids")
        with col2:
            new_email = st.text_input("Email (optional)", placeholder="email@example.com")

        if st.form_submit_button("Add User", type="primary"):
            if not new_name or not new_name.strip():
                render_error_toast("Name is required")
            elif get_user_by_name(new_name.strip()):
                render_error_toast("User with this name already exists")
            else:
                create_user(new_name.strip(), new_email.strip() or None)
                render_success_toast(f"User '{new_name}' added!")
                st.rerun()

st.divider()

# --- User List ---
st.subheader("👤 Users")

users = get_users(active_only=False)  # Show all including inactive

if users:
    for user in users:
        is_current = user.id == current_user_id

        with st.container(border=True):
            u_col1, u_col2, u_col3, u_col4 = st.columns([3, 2, 1, 1])

            with u_col1:
                status = "🟢 Active" if user.is_active else "🔴 Inactive"
                current_badge = " ← **You are here**" if is_current else ""
                st.markdown(f"**{user.name}** {current_badge}")
                st.caption(f"{status} • Created: {user.created_at.strftime('%d/%m/%Y')}")
                if user.email:
                    st.caption(f"📧 {user.email}")

            with u_col2:
                if not is_current:
                    if st.button("🔄 Switch", key=f"switch_{user.id}", use_container_width=True):
                        st.session_state.current_user = user.name
                        st.session_state.current_user_id = user.id
                        render_success_toast(f"Switched to {user.name}")
                        st.rerun()
                else:
                    st.info("Current User")

            with u_col3:
                if user.is_active:
                    if st.button("⏸️ Deactivate", key=f"deact_{user.id}"):
                        if render_confirm_dialog(f"Deactivate {user.name}?", f"deact_{user.id}"):
                            update_user(user.id, is_active=False)
                            render_success_toast(f"{user.name} deactivated")
                            st.rerun()
                else:
                    if st.button("▶️ Activate", key=f"act_{user.id}"):
                        update_user(user.id, is_active=True)
                        render_success_toast(f"{user.name} activated")
                        st.rerun()

            with u_col4:
                if not is_current and not user.is_active:
                    if st.button("🗑️ Delete", key=f"del_user_{user.id}"):
                        if render_confirm_dialog(f"Delete {user.name} permanently?", f"del_user_{user.id}"):
                            # Note: This would need a delete_user function in crud.py
                            # For now, just deactivate
                            render_error_toast("Use deactivate instead. Hard delete not implemented.")
else:
    render_empty_state("No users found. Add your first user above!")

st.divider()

# --- Info ---
st.subheader("ℹ️ How It Works")
st.markdown("""
- **Each user** has their own expenses, categories, and budgets
- **Global categories** (🌐) are shared across all users
- **Personal categories** are only visible to the user who created them
- **Switch users** using the sidebar dropdown or the "Switch" button above
- **Deactivate** a user to hide them from the selector without deleting data
""")