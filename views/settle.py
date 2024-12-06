import os
import pandas as pd
import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt


def settle(history_dir, debts_file):
    st.title("💲Settle💲")
    
    # Check if user moved to other menu
    if st.session_state.state != 'Settle':
        st.session_state.state = 'Settle'

    try:
        # Find the latest history directory
        history_dirs = sorted(
            [d for d in os.listdir(history_dir) if os.path.isdir(os.path.join(history_dir, d))],
            key=lambda x: pd.to_datetime(x, format="%Y-%m-%d_%H-%M-%S"),
            reverse=True,
        )

        if history_dirs:
            latest_history_dir = os.path.join(history_dir, history_dirs[0])
            settle_file = os.path.join(latest_history_dir, "settle.csv")
            current_selections_file = os.path.join(latest_history_dir, "current_selections.csv")
            who_paid_file = os.path.join(latest_history_dir, "who_paid.txt")

            # Ensure settle_data is always initialized
            if os.path.exists(settle_file):
                settle_data = pd.read_csv(settle_file)
            else:
                # Create a new settle.csv file with user names and zero debt
                users = [
                    "Invitado",
                    "Anna",
                    "Carlos Cortés",
                    "Carlos Cuevas",
                    "Carlos Roberto",
                    "Celia Ibáñez",
                    "César Díaz",
                    "Dani Berjón",
                    "Dani Fuertes",
                    "David",
                    "Enmin Zhong",
                    "Enol Ayo",
                    "Francisco Morán",
                    "Javier Usón",
                    "Jesús Gutierrez",
                    "Julián Cabrera",
                    "Isa Rodriguez",
                    "Leyre Encío",
                    "Marcos Rodrigo",
                    "Marta Goyena",
                    "Marta Orduna",
                    "Martina",
                    "Matteo",
                    "Miki",
                    "Narciso García",
                    "Pablo Pérez",
                    "Victoria",
                ]  # Replace with your dynamic user list
                settle_data = pd.DataFrame({"Name": users, "Debt": [0] * len(users)})
                settle_data.to_csv(settle_file, index=False)

            # Check if the who_paid.txt file exists
            if os.path.exists(who_paid_file):
                # If someone has already paid, display the information
                with open(who_paid_file, "r") as file:
                    paid_user = file.read().strip()
                st.subheader(f":red[{paid_user}] paid the last coffees")
            else:
                # Load current_selections.csv
                if os.path.exists(current_selections_file):
                    current_selections = pd.read_csv(current_selections_file)
                    present_users = current_selections["Name"].tolist()
                else:
                    present_users = []

                # Identify who pays for coffees
                settle_data_present = settle_data[settle_data["Name"].isin(present_users)]
                if not settle_data_present.empty:
                    max_debt_user = settle_data_present.loc[settle_data_present["Debt"].idxmax()]["Name"]
                    st.subheader(f"Who pays today: :red[{max_debt_user}]")

                    # Create a confirmation button
                    if "confirm_payment" not in st.session_state:
                        st.session_state.confirm_payment = False

                    # Show the "Paid" button
                    if not st.session_state.confirm_payment:
                        if st.button(f"{max_debt_user} Paid"):
                            st.session_state.confirm_payment = True

                    # Show the confirmation buttons
                    if st.session_state.confirm_payment:
                        st.write(f"Are you sure {max_debt_user} has paid?")
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button("Confirm"):
                                if os.path.exists(debts_file):
                                    debts_data = pd.read_csv(debts_file)
                                    total_spent = debts_data["Spent"].sum()

                                    # Subtract the total spent from the payer's debt and round to 2 decimals
                                    settle_data.loc[settle_data["Name"] == max_debt_user, "Debt"] = round(
                                        settle_data.loc[settle_data["Name"] == max_debt_user, "Debt"].values[0] - total_spent,
                                        2,
                                    )
                                    settle_data.to_csv(settle_file, index=False)

                                    # Write the name of the person who paid to the who_paid.txt file
                                    with open(who_paid_file, "w") as file:
                                        file.write(f"{max_debt_user}\n")

                                    st.success(f"{max_debt_user}'s debt has been updated! Paid {total_spent:.2f}€.")
                                else:
                                    st.warning("No debts file found. Unable to process payment.")
                                st.session_state.confirm_payment = False  # Reset confirmation state
                        with col2:
                            if st.button("Cancel"):
                                st.session_state.confirm_payment = False

            # Draw a bar plot with Seaborn
            plt.figure(figsize=(12, 6))
            sns.barplot(
                data=settle_data,
                x="Name",
                y="Debt",
                hue="Name",  # Assign unique colors based on the "Name" column
                dodge=False,  # Ensures all bars are aligned
                palette="husl",  # Use a color palette
            )
            plt.xlabel("User")
            plt.ylabel("Debt (€)")
            plt.ylim(settle_data["Debt"].min() - 1, settle_data["Debt"].max() + 1)  # Set y-axis limits
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

    except FileNotFoundError:
        st.write("No history records found. Unable to load settle data.")
