import os
import pandas as pd
import streamlit as st
from utils import save_history, save_whopaid, save_order, load_order, load_csv, save_csv, ticket_logic


def current(history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file, last_file):
    st.title("Current 💥")

    # Check if user moved to other view
    if st.session_state.state != "Current":
        st.session_state.state = "Current"
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

    def reload_onclick():
        st.session_state.order_state = 0
        st.session_state.current_df = load_order(order_file)

    # Load current order
    st.session_state.current_df = load_order(order_file)

    # Quick actions at the top
    col1, col2, col3 = st.columns(3)
    with col1:
        st.button("🔄 Reload", on_click=reload_onclick, use_container_width=True)
    with col2:
        st.button("✏️ Edit Order", disabled=st.session_state.order_state < 0, on_click=edit_ticket_onclick, use_container_width=True)
    with col3:
        st.button("🎫 Generate Ticket", disabled=st.session_state.order_state > 0, on_click=get_ticket_onclick, use_container_width=True, type="primary")

    st.divider()

    # Current order section
    st.subheader("📋 Current Order")

    # Show metrics
    num_orders = len(st.session_state.current_df)
    num_people = st.session_state.current_df["Name"].nunique() if num_orders > 0 else 0

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric("Total Orders", num_orders)
    with metric_col2:
        st.metric("Participants", num_people)
    with metric_col3:
        if st.session_state.order_state > 0:
            # Calculate total price only if ticket was generated
            bar_ticket, machine_ticket, debts_ticket = ticket_logic(st.session_state.current_df)
            total_price = sum([float(price) for price in debts_ticket["Debt"]])
            st.metric("Total to Pay", f"{total_price:.2f} €")
        else:
            st.metric("Total to Pay", "—")

    # Display current order
    if num_orders > 0:
        st.dataframe(st.session_state.current_df, hide_index=True, use_container_width=True)
    else:
        st.info("📭 No orders yet. Go to the Poll view to add orders!")

    # Edit mode
    if st.session_state.order_state == -1:
        st.divider()
        with st.container(border=True):
            st.subheader("✏️ Edit Order")

            # Display the multiselect with formatted row strings
            remove_rows = st.multiselect(
                "Select orders to remove:",
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
                st.success("Selected orders removed!", icon="🎉")
                st.session_state.order_state = 0

            # Action buttons
            btn_col1, btn_col2 = st.columns([1, 1])
            with btn_col1:
                st.button("🗑️ Remove Selected", disabled=len(remove_rows) == 0, on_click=remove_onclick, use_container_width=True, type="primary")
            with btn_col2:
                st.button("❌ Cancel", on_click=reload_onclick, use_container_width=True)

    # Ticket generation and payment flow
    if st.session_state.order_state > 0 and num_orders > 0:
        st.divider()

        # Calculate ticket logic
        bar_ticket, machine_ticket, debts_ticket = ticket_logic(st.session_state.current_df)

        # Save tickets
        save_csv(bar_ticket, bar_file)
        save_csv(machine_ticket, machine_file)
        save_csv(debts_ticket, debts_file)

        # Get total price
        total_price = sum([float(price) for price in debts_ticket["Debt"]])

        # Display tickets in tabs
        st.subheader("🎫 Tickets")
        tab1, tab2, tab3 = st.tabs(["📝 Bar Order", "💳 Payment Ticket", "💰 Individual Debts"])

        with tab1:
            st.caption("Items to request at the bar")
            st.dataframe(bar_ticket, hide_index=True, use_container_width=True)

        with tab2:
            st.caption("What appears on the payment machine")
            st.dataframe(machine_ticket, hide_index=True, use_container_width=True)

        with tab3:
            st.caption("How much each person owes")
            st.dataframe(debts_ticket, hide_index=True, use_container_width=True)

        st.divider()

        # Payment section
        st.subheader("💸 Payment")

        # Get historic debts
        last_debts = load_csv(last_file)
        last_debts = pd.merge(debts_ticket.drop(columns=["Debt"]), last_debts, on="Name", how="left")
        last_debts = last_debts.sort_values(by="Debt", ascending=False)

        # Display total prominently
        st.info(f"**Total amount to pay:** {total_price:.2f} €")

        # Decide who pays
        possible_whopays = last_debts.apply(
            lambda row: f"{row['Name']}: {':red[+' if row['Debt'] > 0 else (':green[-' if row['Debt'] < 0 else '')}{abs(row['Debt']):.2f}{' €]' if row['Debt'] != 0 else ' €'}",
            axis=1,
        ).tolist()

        if len(possible_whopays) > 0:
            whopays = st.radio("👤 Who will pay?", possible_whopays, on_change=get_ticket_onclick)

            # Close poll
            if st.button("✅ Close Poll & Save to History", type="primary", disabled=st.session_state.order_state > 1, on_click=close_poll_onclick, use_container_width=True) or st.session_state.order_state > 1:
                if whopays:
                    whopaid = whopays.split(": ")[0]

                    # Confirmation section
                    st.divider()
                    with st.container(border=True):
                        st.warning("⚠️ **Confirmation Required**", icon="⚠️")
                        st.write(f"**{whopaid}** will pay **{total_price:.2f} €**")
                        st.write("This will close the poll and save the order to history. The current order will be cleared.")

                        # Confirm close poll
                        def close_poll():
                            # Save who paid
                            save_whopaid(whopaid_file, whopaid, total_price)

                            # Save data to history
                            timestamp = save_history(history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file, last_file)
                            st.success(f"Poll saved to history at {timestamp}", icon="🎉")

                            # Clear local current selections
                            if os.path.exists(order_file):
                                os.remove(order_file)

                                # Create an empty CSV to replace the deleted one
                                pd.DataFrame(columns=["Name", "Drinks", "Food"]).to_csv(order_file, index=False)

                            # Reset session state for current selections and ticket generation status
                            st.session_state.order_state = 0

                        # Confirm buttons
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            st.button("✔️ Confirm & Close", type="primary", on_click=close_poll, use_container_width=True)
                        with col2:
                            st.button("❌ Cancel", on_click=get_ticket_onclick, use_container_width=True)
