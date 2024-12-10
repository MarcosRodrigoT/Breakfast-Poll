import os
import numpy as np
import pandas as pd
import streamlit as st

from utils import load_history, save_history, save_whopaid, save_order, load_order, get_last_debts, ticket_logic


def current(history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file, backup_file=''):
    st.title("💥Current💥")
    
    # Check if user moved to other view
    if st.session_state.state != 'Current':
        st.session_state.state = 'Current'
        st.session_state.order_state = 0
        st.session_state.current_df = load_order(order_file)

    # Initialize state
    if "order_state" not in st.session_state:
        st.session_state.order_state = 0
    
    # On click events
    def edit_ticket_onclick():
        st.session_state.order_state = -1
    def get_ticket_onclick():
        st.session_state.order_state = 1
    def close_poll_onclick():
        st.session_state.order_state = 2

    # Reload current order
    if st.button("Reload"):
        st.session_state.order_state = 0

    # Load current order
    st.session_state.current_df = load_order(order_file)
    st.dataframe(st.session_state.current_df, hide_index=True, use_container_width=True)

    # Get ticket
    if st.session_state.order_state >= 0:
        if st.button("Get Ticket", disabled=st.session_state.order_state > 0, on_click=get_ticket_onclick) or st.session_state.order_state > 0:

            # Calculate ticket logic
            bar_ticket, machine_ticket, debts_ticket = ticket_logic(st.session_state.current_df)

            # Print tickets
            st.subheader("Items to ask at the bar")
            st.dataframe(bar_ticket, hide_index=True, use_container_width=True)
            st.subheader("Paying Ticket")
            st.dataframe(machine_ticket, hide_index=True, use_container_width=True)
            st.subheader("Debts Ticket")
            st.dataframe(debts_ticket, hide_index=True, use_container_width=True)

            # Save tickets
            bar_ticket.to_csv(bar_file, index=False)
            machine_ticket.to_csv(machine_file, index=False)
            debts_ticket.to_csv(debts_file, index=False)

            # Get total price
            st.header("💸Pay💸")
            total_price = sum([float(price) for price in debts_ticket["Debt"]])
            st.write(f"**Total Price:** {total_price:.2f} €")
            
            # Get historic debts
            historic_debts_, _ = get_last_debts(history_dir, st.session_state.users, backup_file)
            historic_debts = pd.merge(debts_ticket.drop(columns=["Debt"]), historic_debts_, on="Name", how="left")
            historic_debts = historic_debts.sort_values(by="Debt", ascending=False)
            
            # Decide who pays
            possible_whopays = historic_debts.apply(
                lambda row: f"{row['Name']}: "
                            f"{':red[+' if row['Debt'] > 0 else (':green[-' if row['Debt'] < 0 else '')}"
                            f"{abs(row['Debt']):.2f}{' €]' if row['Debt'] != 0 else ' €'}",
                axis=1
            ).tolist()
            whopays = st.radio("Decide who pays:", possible_whopays, on_change=get_ticket_onclick)
            
            # Close poll
            if len(possible_whopays) > 0:
                if (st.button("Close Poll", type="primary", disabled=st.session_state.order_state > 1, on_click=close_poll_onclick) or st.session_state.order_state > 1) and whopays:
                    
                    # Print who pays
                    st.write("")
                    whopaid = whopays.split(': ')[0]
                    st.write(f"**{whopaid} will pay {total_price:.2f} €**")
                    
                    # Display warning
                    st.warning("Warning: Are you sure you want to close the poll? You will delete the current order", icon="⚠️")

                    # Confirm close poll
                    def close_poll():
                        
                        # Save who paid
                        save_whopaid(whopaid_file, whopaid, total_price)
                        
                        # Save data to history
                        timestamp = save_history(st.session_state.users, history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file, backup_file)
                        st.success(f"Poll saved to history at {timestamp}", icon="🎉")
                        st.session_state.history = load_history(history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file)

                        # Clear local current selections
                        if os.path.exists(order_file):
                            os.remove(order_file)

                            # Create an empty CSV to replace the deleted one
                            pd.DataFrame(columns=["Name", "Drinks", "Food"]).to_csv(order_file, index=False)

                        # Reset session state for current selections and ticket generation status
                        st.session_state.order_state = 0
                    
                    # Confirm close poll
                    col1, col2 = st.columns([1, 5])  # Makes the 2nd column 5 times wider than the 1st one
                    with col1:
                        st.button("Confirm", type="primary", on_click=close_poll)
                    with col2:
                        st.button("Cancel", on_click=get_ticket_onclick)

    # Edit ticket allows removing rows from current order
    if st.session_state.order_state <= 0:
        if st.button("Edit Ticket", disabled=st.session_state.order_state < 0, on_click=edit_ticket_onclick) or st.session_state.order_state == -1:
            
            # Display the multiselect with formatted row strings
            remove_rows = st.multiselect(
                "Select rows to remove:",
                options=st.session_state.current_df.index,
                format_func=lambda idx: f"{st.session_state.current_df.loc[idx, 'Name']} - {st.session_state.current_df.loc[idx, 'Drinks']} - {st.session_state.current_df.loc[idx, 'Food']}",
            )

            # Remove selected rows on button click
            def remove_onclick():
                # Remove rows
                st.session_state.current_df = st.session_state.current_df.drop(index=remove_rows).reset_index(drop=True)
                
                # Save new dataframe
                save_order(st.session_state.current_df, order_file, combine=False)
                
                # Remove tmp data
                if os.path.exists(bar_file):
                    os.remove(bar_file)
                if os.path.exists(machine_file):
                    os.remove(machine_file)
                if os.path.exists(debts_file):
                    os.remove(debts_file)
                
                # Print success and exit
                st.success("Selected rows removed!", icon="🎉")
                st.session_state.order_state = 0
            
            # Remove button
            st.button("Remove", disabled=len(remove_rows) == 0, on_click=remove_onclick)
    