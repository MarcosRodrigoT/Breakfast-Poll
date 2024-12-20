import os
import pandas as pd
import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt

from utils import load_debts, load_users, save_users


def debts(history_dir, users_file, debts_file, backup_file=''):
    st.title("Debts 💲")
    
    # Check if user moved to other menu
    if st.session_state.state != 'Debts':
        st.session_state.state = 'Debts'
        st.session_state.users = load_users(users_file)
        st.session_state.user_msg = {}
        st.session_state.new_user = ''
        st.session_state.new_debt = 0.0

    # Find the latest history directory
    history_dirs = sorted(
        [d for d in os.listdir(history_dir) if os.path.isdir(os.path.join(history_dir, d))],
        key=lambda x: pd.to_datetime(x, format="%Y-%m-%d_%H-%M-%S"),
        reverse=True,
    )

    # Load last historic debts
    if len(history_dirs) > 0:
        latest_history_dir = os.path.join(history_dir, history_dirs[0])
        debts_file = os.path.join(latest_history_dir, "debts.csv")
    else:
        debts_file = ""
    debts_data = load_debts(debts_file, st.session_state.users, backup_file)

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
                number = '🥇'
            case 1:
                number = '🥈'
            case 2:
                number = '🥉'
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
    st.session_state.new_debt = st.number_input(
        "Enter the starting debt for the user:", format="%.2f"
    )
    if len(st.session_state.new_user) > 0:
        st.write(f"User {st.session_state.new_user} will be added, with debt {st.session_state.new_debt} €")
    
    # Handle success/warning onclick
    if 'user_msg' not in st.session_state:
        st.session_state.user_msg = {}
    if 'success' in st.session_state.user_msg:
        st.success(st.session_state.user_msg['success'], icon="🎉")
        st.session_state.user_msg = {}
    if 'warning' in st.session_state.user_msg:
        st.warning(st.session_state.user_msg['warning'], icon="⚠️")
        st.session_state.user_msg = {}
    
    # Add user onclick
    def add_user_onclick():
        if st.session_state.new_user not in st.session_state.users:
            
            # Add starting debt
            if os.path.exists(backup_file):
                backup_data = pd.read_csv(backup_file)
                
                # Check if user is in backup file
                if st.session_state.new_user not in backup_data['Name'].values:
                    
                    # Add debt
                    new_row = pd.DataFrame({"Name": [st.session_state.new_user], "Debt": [st.session_state.new_debt]})
                    updated_backup = pd.concat([backup_data, new_row], ignore_index=True)
                    updated_backup = updated_backup.sort_values(
                        by="Name",
                        key=lambda x: x.map(lambda name: (name != "Invitado", name))
                    )
                    updated_backup.to_csv(backup_file, index=False)
                    
                    # Add user
                    st.session_state.users.append(st.session_state.new_user)
                    st.session_state.users = sorted(st.session_state.users, key=lambda x: (x != "Invitado", x))
                    save_users(st.session_state.users, users_file)
                    
                    st.session_state.user_msg['success'] = f"User '{st.session_state.new_user}' added successfully with debt {st.session_state.new_debt:.2f} €!"
                else:
                    st.session_state.user_msg['warning'] = f"User '{st.session_state.new_user}' already exists in {backup_file}. User not added."
            else:
                st.session_state.user_msg['warning'] = f"Backup file '{backup_file}' does not exist. User not added."
        else:
            st.session_state.user_msg['warning'] = f"User '{st.session_state.new_user}' already exists in {users_file}. User not added."

    # Add user button
    st.button("Add User", disabled=len(st.session_state.new_user) == 0 or len(str(st.session_state.new_debt)) == 0, on_click=add_user_onclick)
