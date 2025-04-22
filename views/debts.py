import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt

from utils import load_csv, load_users, add_user


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

    # Add user
    st.header("Add a New User")
    st.session_state.new_user = st.text_input("Enter the new user's name:")
    st.session_state.new_user = st.session_state.new_user.strip()
    st.session_state.new_debt = st.number_input("Enter the starting debt for the user:", format="%.2f")
    st.session_state.new_desc = st.text_input("Enter a description for the user:")
    if len(st.session_state.new_user) > 0:
        st.write(f"{st.session_state.new_user} will be added with debt {st.session_state.new_debt} € and the following description:")
        st.write(st.session_state.new_desc)

    # Handle success/warning onclick
    if "user_msg" not in st.session_state:
        st.session_state.user_msg = {}
    if "success" in st.session_state.user_msg:
        st.success(st.session_state.user_msg["success"], icon="🎉")
        st.session_state.user_msg = {}
    if "warning" in st.session_state.user_msg:
        st.warning(st.session_state.user_msg["warning"], icon="⚠️")
        st.session_state.user_msg = {}

    # Add user onclick
    def add_user_onclick():
        result = add_user(users_file, st.session_state.new_user, st.session_state.new_debt, st.session_state.new_desc, last_file)
        st.session_state.users = load_users(users_file)
        if result:
            st.session_state.user_msg["success"] = f"User '{st.session_state.new_user}' added successfully with debt {st.session_state.new_debt:.2f} €!"
        else:
            st.session_state.user_msg["warning"] = f"User '{st.session_state.new_user}' already exists in {users_file} or in {last_file}. User not added."

    # Add user button
    st.button("Add User", disabled=len(st.session_state.new_user) == 0 or len(str(st.session_state.new_debt)) == 0, on_click=add_user_onclick)
