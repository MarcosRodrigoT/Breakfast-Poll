import pandas as pd
import streamlit as st
from utils import save_order, add_user, load_users, load_active_users, load_hidden_users, toggle_user_status


def poll(order_file, users_file, last_file):
    st.title("Poll ☕")

    # Add new user
    with st.expander("➕  Add a new user"):
        new_user = st.text_input("User name", key="poll_new_user").strip()
        new_debt = st.number_input("Starting debt (€)", format="%.2f", key="poll_new_debt")

        if len(new_user) > 0:
            st.write(f"**Preview:** {new_user} → {new_debt:.2f} €")

        def add_user_onclick():
            ok = add_user(users_file, new_user, new_debt, last_file)
            if ok:
                # refresh the in‑memory list and let Streamlit re‑run
                st.session_state.users = load_users(users_file)
                st.success(f"User “{new_user}” added! 🎉")
                # clear widgets for convenience
                st.session_state.poll_new_user = ""
                st.session_state.poll_new_debt = 0.0
            else:
                st.warning(f"User “{new_user}” already exists.", icon="⚠️")

        st.button("Save user", disabled=len(new_user) == 0, on_click=add_user_onclick)

    # Manage hidden users
    with st.expander("👁️ Manage Hidden Users"):
        st.markdown("**Hide inactive users** to keep the participant list short. Hidden users can still be unhidden later.")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Active Users")
            active_users = load_active_users(users_file)

            if active_users:
                for user in active_users:
                    col_user, col_btn = st.columns([3, 1])
                    with col_user:
                        st.write(user)
                    with col_btn:
                        if st.button("Hide", key=f"hide_{user}"):
                            toggle_user_status(users_file, user, "hidden")
                            st.session_state.users = load_users(users_file)
                            st.rerun()
            else:
                st.info("No active users")

        with col2:
            st.subheader("Hidden Users")
            hidden_users = load_hidden_users(users_file)

            if hidden_users:
                for user in hidden_users:
                    col_user, col_btn = st.columns([3, 1])
                    with col_user:
                        st.write(user)
                    with col_btn:
                        if st.button("Show", key=f"show_{user}"):
                            toggle_user_status(users_file, user, "active")
                            st.session_state.users = load_users(users_file)
                            st.rerun()
            else:
                st.info("No hidden users")

    def step1_onclick():
        st.session_state.poll_state = 0

    def step2_onclick():
        st.session_state.poll_state = 1

    def step3_onclick():
        st.session_state.poll_state = 2

    # Check if user moved to other view
    if st.session_state.state != "Poll":
        st.session_state.state = "Poll"
        st.session_state.poll_state = 0
        st.session_state.success = False

    # Initialize state
    if "poll_state" not in st.session_state:
        st.session_state.poll_state = 0

    # Step 1: Participant
    st.header("Add participant")
    # Load only active users for the poll view
    active_users = load_active_users(users_file)
    participant = st.radio(label="Select your name:", options=active_users, on_change=step1_onclick)

    # Select participant
    if st.button("Next", key="step1_next", disabled=st.session_state.poll_state > 0, on_click=step2_onclick):
        st.session_state.poll_state = 1
        st.session_state.current_order = {"Name": participant}

    # Step 2: Drink (only if step 1 completed)
    if st.session_state.poll_state > 0:
        st.header("Select your drink")
        drinks_options = [
            "Nada",
            "Aguasusia",
            "Aguasusia susia",
            "Café con leche",
            "Café con soja",
            "Café sin lactosa",
            "Colacao",
            "Cortado",
            "Descafeinado con leche",
            "Descafeinado con leche desnatada",
            "Italiano",
            "Manzanilla",
            "Té",
            "Té con leche",
        ]
        drink = st.radio("Choose your drinks:", drinks_options, on_change=step2_onclick)

        # Select drink
        if st.button("Next", key="step2_next", disabled=st.session_state.poll_state > 1, on_click=step3_onclick):
            st.session_state.current_order["Drinks"] = drink
            st.session_state.poll_state = 2

    # Print success message here if poll was saved successfully
    if "success" not in st.session_state:
        st.session_state.success = False
    else:
        if st.session_state.success:
            st.success(f"Selections saved for {st.session_state.current_order['Name']}!", icon="🎉")
            st.session_state.success = False

    # Step 3: Food (only if step 2 completed)
    if st.session_state.poll_state > 1:
        st.header("Select your food")
        food_options = [
            "Nada",
            "Barrita aceite",
            "Barrita tomate",
            "Croissant plancha",
            "Napolitana de chocolate",
            "Palmera chocolate",
            "Palmera chocolate blanco",
            "Tortilla",
            "Yogurt",
        ]
        food = st.radio("Choose your food:", food_options)

        # Save selections on click
        def save_onclick():
            st.session_state.current_order["Food"] = food

            # Save selections
            df = pd.DataFrame(st.session_state.current_order, index=[0])
            save_order(df, order_file)

            # Success & reset
            st.session_state.success = True
            st.session_state.poll_state = 0

        # Select food button
        st.button("Save", on_click=save_onclick)
