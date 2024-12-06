import streamlit as st
from datetime import datetime
from utils import load_history, format_date


def history(history_dir, selections_file, bar_file, machine_file, debts_file):
    st.title("📜History📜")
    
    # Check if user moved to other menu
    if st.session_state.state != 'History':
        st.session_state.state = 'History'

    # Load history if it's not already loaded
    st.session_state.history = load_history(history_dir, selections_file, bar_file, machine_file, debts_file)

    # Sort history by the Date key in descending order
    st.session_state.history = sorted(st.session_state.history, key=lambda x: datetime.strptime(x["Date"], "%Y-%m-%d_%H-%M-%S"), reverse=True)

    if st.session_state.history:
        # Display history in reverse chronological order
        for record in st.session_state.history:
            # Format the date for display
            formatted_date = format_date(record["Date"])
            with st.expander(f"{formatted_date}"):
                st.markdown("#### Selections")
                st.dataframe(record["Selection"], hide_index=True, use_container_width=True)
                st.markdown("#### Bar")
                st.dataframe(record["Bar"], hide_index=True, use_container_width=True)
                st.markdown("#### Machine")
                st.dataframe(record["Machine"], hide_index=True, use_container_width=True)
                st.markdown("#### Debts")
                st.dataframe(record["Debts"], hide_index=True, use_container_width=True)

    else:
        st.write("No history records found.")
