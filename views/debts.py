import streamlit as st
import plotly.express as px
from utils import load_users, load_current_debts


def debts(users_file, last_file):
    st.title("Debts 💲")

    # Check if user moved to other menu
    if st.session_state.state != "Debts":
        st.session_state.state = "Debts"
        st.session_state.users = load_users(users_file)
        st.session_state.user_msg = {}
        st.session_state.new_user = ""
        st.session_state.new_debt = 0.0
        st.session_state.new_desc = ""

    debts_data = load_current_debts()

    # Sort by debt (descending - highest debt first)
    debts_data_sorted = debts_data.sort_values(by="Debt", ascending=True).reset_index(drop=True)

    # Calculate dynamic height based on number of users (30px per user, minimum 400px)
    chart_height = max(400, len(debts_data_sorted) * 30)

    # Create horizontal bar chart with diverging color scale
    # Red for high debt (positive), white for ~0, green for overpayment (negative)
    fig = px.bar(
        debts_data_sorted,
        x="Debt",
        y="Name",
        orientation="h",
        title="Current Debt by User",
        color="Debt",
        color_continuous_scale="RdYlGn_r",  # Red-Yellow-Green reversed (red for positive, green for negative)
        color_continuous_midpoint=0,  # Center the color scale at 0
        labels={"Debt": "Debt (€)", "Name": "User"}
    )

    fig.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        height=chart_height,
        xaxis_title="Debt (€)",
        yaxis_title="User"
    )

    # Add vertical line at x=0 to show the debt/credit boundary
    fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.7, line_width=2)

    st.plotly_chart(fig, use_container_width=True)

    st.caption("💡 Red indicates debt owed, green indicates overpayment/credit")

    st.divider()

    # Sort by debt
    sorted_debts = debts_data.sort_values(by="Debt", ascending=False).reset_index(drop=True)

    # Print each row
    st.header("Podium")
    for idx, row in sorted_debts.iterrows():
        # Get number
        match idx:
            case 0:
                number = "🥇"
            case 1:
                number = "🥈"
            case 2:
                number = "🥉"
            case _:
                number = f"{idx + 1}."

        # Print name and debt in 2 columns
        col1, col2 = st.columns([1, 3])  # Makes the 2nd column 3 times wider than the 1st one
        with col1:
            st.write(f"{number} {row['Name']}")
        with col2:
            debt_sign = f"{':red[+' if row['Debt'] > 0 else (':green[-' if row['Debt'] < 0 else '')}"
            debt_value = f"{abs(row['Debt']):.2f}{' €]' if row['Debt'] != 0 else ' €'}"
            st.write(f"{debt_sign} {debt_value}")
