import streamlit as st
from datetime import datetime
from utils import load_history, format_date


def history(history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file):
    st.title("📜History📜")
    
    # Check if user moved to other menu
    if st.session_state.state != 'History':
        st.session_state.state = 'History'

    # Load history if it's not already loaded
    history = load_history(history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file)

    # Sort history by the date key in descending order
    history = sorted(history, key=lambda x: datetime.strptime(x["Date"], "%Y-%m-%d_%H-%M-%S"), reverse=True)

    # Display history in reverse chronological order
    if history:
        for record in history:
            
            # Format the date for display
            formatted_date = format_date(record["Date"])
            
            # Show data
            with st.expander(f"{formatted_date}"):
                st.markdown("#### Order")
                st.dataframe(record["Order"], hide_index=True, use_container_width=True)
                st.markdown("#### Bar")
                st.dataframe(record["Bar"], hide_index=True, use_container_width=True)
                st.markdown("#### Machine")
                st.dataframe(record["Machine"], hide_index=True, use_container_width=True)
                st.markdown("#### Who Paid")
                name, price = record["Whopaid"]
                st.write(f"**{name} paid {price:.2f} €**")
                st.markdown("#### Debts")
                st.dataframe(record["Debts"], hide_index=True, use_container_width=True)

    else:
        st.write("No history records found.")
