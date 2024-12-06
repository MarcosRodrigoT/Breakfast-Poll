import os
import pandas as pd
import streamlit as st

from utils import load_history, load_order, save_history, save_whopaid, ticket_logic


def current(history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file):
    st.title("💥Current💥")
    
    # Check if user moved to other view
    if st.session_state.state != 'Current':
        st.session_state.state = 'Current'
        st.session_state.order_state = 0

    # Initialize state
    if "order_state" not in st.session_state:
        st.session_state.order_state = 0
    
    # On click events
    def get_ticket_onclick():
        st.session_state.order_state = 1
    def close_poll_onclick():
        st.session_state.order_state = 2

    # Reload current order
    if st.button("Reload"):
        st.session_state.order_state = 0

    # Load current order
    current_df = load_order(order_file)
    st.dataframe(current_df, hide_index=True, use_container_width=True)

    # Get ticket
    if st.button("Get Ticket", disabled=st.session_state.order_state > 0, on_click=get_ticket_onclick) or st.session_state.order_state > 0:

        # Calculate ticket logic
        bar_ticket, machine_ticket, debts_ticket = ticket_logic(current_df)

        # Print tickets
        st.subheader("Items to ask at the bar")
        st.dataframe(bar_ticket, hide_index=True, use_container_width=True)
        st.subheader("Paying Ticket")
        st.dataframe(machine_ticket, hide_index=True, use_container_width=True)
        st.subheader("Settle Up Ticket")
        st.dataframe(debts_ticket, hide_index=True, use_container_width=True)

        # Save tickets
        bar_ticket.to_csv(bar_file, index=False)
        machine_ticket.to_csv(machine_file, index=False)
        debts_ticket.to_csv(debts_file, index=False)

        # Get total price
        st.header("💸Pay💸")
        total_price = sum([float(price) for price in debts_ticket["Spent"]])
        st.write(f"**Total Price:** {total_price:.2f} €")
        
        # Decide who pays
        debts_ticket = debts_ticket.sort_values(by="Spent", ascending=False)
        possible_whopays = debts_ticket.apply(lambda row: f"{row['Name']} - {row['Spent']}", axis=1).tolist()
        whopays = st.radio("Decide who pays:", possible_whopays, on_change=get_ticket_onclick)
        
        # Close poll
        if len(possible_whopays) > 0:
            if (st.button("Close Poll", type="primary", disabled=st.session_state.order_state > 1, on_click=close_poll_onclick) or st.session_state.order_state > 1) and whopays:
                
                # Print who pays
                st.write("")
                whopaid = whopays.split(' - ')[0]
                st.write(f"**{whopaid} will pay {total_price:.2f} €**")
                
                # Display warning
                st.warning("Warning: Are you sure you want to close the poll? You will delete the current order", icon="⚠️")

                # Confirm close poll
                def close_poll():
                    
                    # Save who paid
                    save_whopaid(whopaid_file, whopaid, total_price)
                    
                    # Save data to history
                    timestamp = save_history(st.session_state.users, history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file)
                    st.success(f"Poll saved to history at {timestamp}")
                    st.session_state.history = load_history(history_dir, order_file, bar_file, machine_file, debts_file)

                    # Clear local current selections
                    if os.path.exists(order_file):
                        os.remove(order_file)

                        # Create an empty CSV to replace the deleted one
                        pd.DataFrame(columns=["Name", "Drinks", "Food"]).to_csv(order_file, index=False)

                    # Reset session state for current selections and ticket generation status
                    st.session_state.order_state = 0
                
                # Confirm close poll
                st.button("Confirm", type="primary", on_click=close_poll)
