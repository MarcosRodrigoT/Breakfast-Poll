import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt
from utils import load_csv, load_users


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

    # Find the latest history directory
    debts_data = load_csv(last_file)

    # Draw a bar plot with Seaborn
    plt.figure(figsize=(12, 6))
    sns.barplot(
        data=debts_data,
        x="Name",
        y="Debt",
        hue="Name",  # Assign unique colors based on the "Name" column
        dodge=False,  # Ensures all bars are aligned
        palette="husl",  # Use a color palette
    )
    plt.xlabel("User")
    plt.ylabel("Debt (€)")
    plt.ylim(debts_data["Debt"].min() - 1, debts_data["Debt"].max() + 1)  # Set y-axis limits
    plt.axhline(0, color="black", linestyle="--", linewidth=1)  # Draw horizontal line at y=0

    # Add a semi-transparent grid
    plt.grid(
        which="major",
        linestyle="--",
        linewidth=0.5,
        alpha=0.7,  # Semi-transparency
    )

    plt.title("Current Debt by User")
    plt.xticks(rotation=45, ha="right")
    plt.legend([], [], frameon=False)  # Hide the legend
    st.pyplot(plt.gcf())

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
