import pandas as pd
import streamlit as st
from utils import save_order


def poll(order_file):
    st.title("Poll ☕")

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
    participant = st.radio(label="Select your name:", options=st.session_state.users, on_change=step1_onclick)

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
