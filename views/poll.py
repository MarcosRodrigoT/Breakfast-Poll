import os
import pandas as pd
import streamlit as st

from utils import save_current_selections


def poll(selections_file):
    st.title("☕Poll☕")
    
    # Check if user moved to other menu
    if st.session_state.state != 'Poll':
        st.session_state.state = 'Poll'
        st.session_state.poll_state = 0
        st.session_state.participant = st.session_state.users[0]
    
    # Initialize state
    if "poll_state" not in st.session_state:
        st.session_state.poll_state = 0
    
    # Initialize default participant
    if "participant" not in st.session_state:
        st.session_state.participant = st.session_state.users[0]

    # Step 1: Participant
    st.header("Add participant")
    participant = st.radio(
        label="Select your name:",
        options=st.session_state.users,
        index=st.session_state.users.index(st.session_state.participant)
    )
    
    # Select participant
    if st.button("Next", key="step1_next") and participant:
        st.session_state.participant = participant
        st.session_state.poll_state = 1
        st.session_state.current_selections = {"Name": participant}

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
        ]
        drink = st.radio("Choose your drinks:", drinks_options)

        # Select drink
        if st.button("Next", key="step2_next") and drink:
            st.session_state.current_selections['Drinks'] = drink
            st.session_state.poll_state = 2

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

        # Select food
        if st.button("Save") and food:
            st.session_state.current_selections['Food'] = food
            
            # Save selections
            df = pd.DataFrame(st.session_state.current_selections, index=[0])
            save_current_selections(df, selections_file)
            
            # Success & reset
            st.success(f"Selections saved for {st.session_state.current_selections['Name']}!")
            st.session_state.poll_state = 0
