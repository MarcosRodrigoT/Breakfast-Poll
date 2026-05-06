import streamlit as st
from utils import format_date
from utils.db_utils import load_sessions_page, count_sessions

PAGE_SIZE = 15


def history(history_dir, whopaid_file, order_file, bar_file, machine_file, debts_file):
    st.title("History 📜")

    # Reset pagination state whenever the user navigates to this view
    if st.session_state.state != "History":
        st.session_state.state = "History"
        st.session_state.history_items = []
        st.session_state.history_offset = 0
        st.session_state.history_exhausted = False

    if "history_items" not in st.session_state:
        st.session_state.history_items = []
        st.session_state.history_offset = 0
        st.session_state.history_exhausted = False

    def _load_more():
        new_items = load_sessions_page(st.session_state.history_offset, PAGE_SIZE)
        for record in new_items:
            record["Debts"]["Debt"] = record["Debts"]["Debt"].apply(lambda x: f"{x:.2f}")
        st.session_state.history_items.extend(new_items)
        st.session_state.history_offset += len(new_items)
        if len(new_items) < PAGE_SIZE:
            st.session_state.history_exhausted = True

    # Load the first batch on initial render
    if not st.session_state.history_items:
        _load_more()

    total = count_sessions()
    loaded = len(st.session_state.history_items)
    st.caption(f"Showing {loaded} of {total} sessions")

    if st.session_state.history_items:
        for record in st.session_state.history_items:
            with st.expander(format_date(record["Date"])):
                st.markdown("#### Who Paid")
                name, price = record["Whopaid"]
                st.write(f"**{name} paid {price:.2f} €**")
                st.markdown("#### Order")
                st.dataframe(record["Order"], hide_index=True, use_container_width=True)
                st.markdown("#### Bar")
                st.dataframe(record["Bar"], hide_index=True, use_container_width=True)
                st.markdown("#### Machine")
                st.dataframe(record["Machine"], hide_index=True, use_container_width=True)
                st.markdown("#### Debts")
                st.dataframe(record["Debts"], hide_index=True, use_container_width=True)

        if not st.session_state.history_exhausted:
            remaining = total - loaded
            st.button(
                f"Load more ({remaining} remaining)",
                on_click=_load_more,
                use_container_width=True,
            )
    else:
        st.write("No history records found.")
