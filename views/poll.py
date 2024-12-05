import os
import pandas as pd
import streamlit as st

from utils import save_current_selection_to_file


def poll(selections_file):
    st.title("☕Poll☕")
    
    # Initialize state
    if "poll_state" not in st.session_state:
        st.session_state.poll_state = 0

    # Step 1: User's Name
    st.header("Add participant")
    name_options = [
        "Invitado",
        "Anna",
        "Carlos Cortés",
        "Carlos Cuevas",
        "Carlos Roberto",
        "Celia Ibáñez",
        "César Díaz",
        "Dani Berjón",
        "Dani Fuertes",
        "David",
        "Enmin Zhong",
        "Enol Ayo",
        "Francisco Morán",
        "Javier Usón",
        "Jesús Gutierrez",
        "Julián Cabrera",
        "Isa Rodriguez",
        "Leyre Encío",
        "Marcos Rodrigo",
        "Marta Goyena",
        "Marta Orduna",
        "Martina",
        "Matteo",
        "Miki",
        "Narciso García",
        "Pablo Pérez",
        "Victoria",
    ]
    selected_user = st.radio("Select your name:", name_options)
    if st.button("Next", key="step1_next") and selected_user:
        st.session_state.users.append(selected_user)
        st.session_state.poll_state = 1

    # Show Step 2 only if Step 1 is completed
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
        selected_drinks = st.radio("Choose your drinks:", drinks_options)

        if st.button("Next", key="step2_next") and selected_drinks:
            st.session_state.current_selections.append({
                "Name": st.session_state.users[-1],
                "Drinks": selected_drinks
            })
            st.session_state.poll_state = 2

    # Show Step 3 only if Step 2 is completed
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
        selected_food = st.radio("Choose your food:", food_options)

        if st.button("Save Selections", key="save_selections") and selected_food:
            st.session_state.current_selections[-1]["Food"] = selected_food
            df = pd.DataFrame(st.session_state.current_selections)
            save_current_selection_to_file(df, selections_file)
            st.success(f"Selections saved for {st.session_state.users[-1]}!")
            st.session_state.poll_state = 0
