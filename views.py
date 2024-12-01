import os
import streamlit as st
import pandas as pd
from collections import Counter
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from utils import load_history, save_current_selection_to_file, load_current_selections, save_summary_to_history, format_date


def poll(selections_file):
    st.title("☕Poll☕")

    # Step 1: User's Name
    st.header("Add participant")
    name_options = [
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
    ]
    selected_user = st.radio("Select your name:", name_options)
    if st.button("Next", key="step1_next") and selected_user:
        st.session_state.users.append(selected_user)
        st.session_state.step = 2  # Set the next step to be visible

    # Show Step 2 only if Step 1 is completed
    if st.session_state.step >= 2:
        st.header("Select your drink")
        drinks_options = [
            "Nada",
            "Aguasusia",
            "Aguasusia susia",
            "Café con leche",
            "Café con soja",
            "Café sin lactosa",
            "Colacao",
            "Cortado",
            "Descafeinado con leche",
            "Descafeinado con leche desnatada",
            "Italiano",
            "Manzanilla",
            "Té",
        ]
        selected_drinks = st.radio("Choose your drinks:", drinks_options)

        if st.button("Next", key="step2_next") and selected_drinks:
            st.session_state.current_selections.append({"Name": st.session_state.users[-1], "Drinks": selected_drinks})
            st.session_state.step = 3  # Set the next step to be visible

    # Show Step 3 only if Step 2 is completed
    if st.session_state.step >= 3:
        st.header("Select your food")
        food_options = [
            "Nada",
            "Barrita aceite",
            "Barrita tomate",
            "Croissant plancha",
            "Napolitana de chocolate",
            "Palmera chocolate",
            "Palmera chocolate blanco",
            "Tortilla",
            "Yogurt",
        ]
        selected_food = st.radio("Choose your food:", food_options)

        if st.button("Save Selections", key="save_selections") and selected_food:
            st.session_state.current_selections[-1]["Food"] = selected_food
            df = pd.DataFrame(st.session_state.current_selections)
            save_current_selection_to_file(df, selections_file)
            st.success(f"Selections saved for {st.session_state.users[-1]}!")
            st.session_state.step = 1  # Reset to step 1 for the next user


def current(history_dir, selections_file, bar_file, machine_file, debts_file):
    st.title("💥Current💥")

    if st.button("Reload Selections"):
        # Reload the current selections from the local file
        st.session_state.current_selections = load_current_selections(selections_file).to_dict(orient="records")
        st.success("Selections reloaded successfully!")

    # Load the current selections from the session state or from the file
    current_df = load_current_selections(selections_file)
    st.dataframe(current_df, hide_index=True, use_container_width=True)

    # Define item prices and categories
    item_prices = {
        "Café con leche": (1.2, "Café"),
        "Cortado": (1.2, "Café"),
        "Italiano": (1.2, "Café"),
        "Aguasusia": (1.2, "Café"),
        "Café sin lactosa": (1.2, "Café"),
        "Café con soja": (1.2, "Café"),
        "Descafeinado con leche": (1.2, "Café"),
        "Descafeinado con leche desnatada": (1.2, "Café"),
        "Aguasusia susia": (1.2, "Café"),
        "Colacao": (1.5, "Colacao"),
        "Té": (0.9, "Infusión"),
        "Manzanilla": (0.9, "Infusión"),
        "Barrita aceite": (1.85, "Barrita aceite"),
        "Barrita tomate": (2.5, "Barrita tomate"),
        "Napolitana de chocolate": (1.85, "Napolitana"),
        "Croissant plancha": (2.5, "Croissant"),
        "Palmera chocolate": (1.5, "Palmera"),
        "Palmera chocolate blanco": (1.5, "Palmera"),
        "Tortilla": (1.5, "Tortilla"),
        "Yogurt": (1.5, "Yogurt"),
        "Nada": (0.0, "Nada"),
    }

    # Define possible combos:
    combinable = [
        "Café",
        "Infusión",
        "Barrita aceite",
        "Barrita tomate",
        "Napolitana de chocolate",
        "Croissant plancha",
    ]

    # Use session state to persist ticket generation status
    if "ticket_generated" not in st.session_state:
        st.session_state.ticket_generated = False

    # Generate Ticket Button and Logic
    if st.button("Generate Ticket"):
        ticket = []

        # Iterate over each user's selections
        users = []  # Users that have answer the poll
        drinks = []  # Drinks selected in the poll
        foods = []  # Foods selected in the poll
        variable_users = []  # Users whose price might change depending on combo conditions
        drinker = []  # Users that have gotten a drink and whose price might change depending on combo conditions
        combo_users = []  # Users that have gotten a combo option

        for _, row in current_df.iterrows():
            drinks.append(row["Drinks"])
            foods.append(row["Food"])

            user_name = row["Name"]
            user_drink = row["Drinks"]
            user_food = row["Food"]

            # If just a drink has been selected
            if user_drink != "Nada" and user_food == "Nada":
                user_price = item_prices[user_drink][0]

            # If both drink and food have been selected
            elif user_drink != "Nada" and user_food != "Nada":
                # If chosen food can be combined
                if user_food in combinable:
                    user_food_aux = item_prices[user_food][1]  # Category to which the selected food belongs to
                    user_drink_aux = item_prices[user_drink][1]  # Category to which the selected drink belongs to

                    # If chosen drink can be combined
                    if user_drink_aux in combinable:
                        match user_drink_aux:
                            # If chosen drink is a coffee
                            case "Café":
                                match user_food_aux:
                                    # If chosen food belongs to the cheaper breakfast combo
                                    case "Barrita aceite" | "Napolitana":
                                        user_price = 1.85
                                        combo_users.append((user_name, user_drink, user_food))
                                    # If chosen food belongs to the expensier breakfast combo
                                    case "Barrita tomate" | "Croissant":
                                        user_price = 2.5
                                        combo_users.append((user_name, user_drink, user_food))
                            # If chosen drink is an infusion
                            case "Infusión":
                                match user_food_aux:
                                    # If chosen food belongs to the cheaper breakfast combo
                                    case "Barrita aceite" | "Napolitana":
                                        user_price = (1.85, 1.55)
                                        variable_users.append(user_name)
                                        drinker.append(user_name)
                                        combo_users.append((user_name, user_drink, user_food))
                                    # If chosen food belongs to the expensier breakfast combo
                                    case "Barrita tomate" | "Croissant":
                                        user_price = (2.5, 2.2)
                                        variable_users.append(user_name)
                                        drinker.append(user_name)
                                        combo_users.append((user_name, user_drink, user_food))

                    # If chosen drink cannot be combined
                    else:
                        match user_food_aux:
                            # If chosen food belongs to the cheaper breakfast combo
                            case "Barrita aceite" | "Napolitana":
                                user_price = (item_prices[user_drink][0] + item_prices[user_food][0], 2.15)
                                variable_users.append(user_name)
                                drinker.append(user_name)
                            # If chosen food belongs to the expensier breakfast combo
                            case "Barrita tomate" | "Croissant":
                                user_price = (item_prices[user_drink][0] + item_prices[user_food][0], 2.8)
                                variable_users.append(user_name)
                                drinker.append(user_name)

                # If chosen food cannot be combined
                else:
                    user_price = item_prices[user_drink][0] + item_prices[user_food][0]

            # If just a food has been selected
            else:
                # If chosen food can be combined
                if user_food in combinable:
                    user_food_aux = item_prices[user_food][1]
                    match user_food_aux:
                        # If chosen food belongs to the cheaper breakfast combo
                        case "Barrita aceite" | "Napolitana":
                            user_price = (item_prices[user_food][0], 0.65, 0.95)
                            variable_users.append(user_name)
                        # If chosen food belongs to the expensier breakfast combo
                        case "Barrita tomate" | "Croissant":
                            user_price = (item_prices[user_food][0], 1.3, 1.6)
                            variable_users.append(user_name)

                # If chosen food cannot be combined
                else:
                    user_price = item_prices[user_food][0]

            user_total = (user_name, user_price)
            users.append(user_total)

        # Count items that have to be asked at the bar
        sorted_drinks = sorted(drinks)
        sorted_foods = sorted(foods)
        bar_items = sorted_drinks + sorted_foods
        # st.write(f"Items: {bar_items}")
        bar_count = Counter(bar_items)
        bar_count_dict = dict(bar_count)

        # Simplify items
        drinks = [item_prices[x][1] for x in drinks]
        foods = [item_prices[x][1] for x in foods]

        # Count items
        item_count = {
            "Café": len([x for x in drinks if x == "Café"]),
            "Colacao": len([x for x in drinks if x == "Colacao"]),
            "Infusión": len([x for x in drinks if x == "Infusión"]),
            "Barrita aceite": len([x for x in foods if x == "Barrita aceite"]),
            "Barrita tomate": len([x for x in foods if x == "Barrita tomate"]),
            "Napolitana": len([x for x in foods if x == "Napolitana"]),
            "Croissant": len([x for x in foods if x == "Croissant"]),
            "Palmera": len([x for x in foods if x == "Palmera"]),
            "Tortilla": len([x for x in foods if x == "Tortilla"]),
            "Yogurt": len([x for x in foods if x == "Yogurt"]),
        }

        # Make associations
        item_association = {}
        user_association = {}
        # Number of combinable food items
        food_count = item_count["Barrita aceite"] + item_count["Barrita tomate"] + item_count["Napolitana"] + item_count["Croissant"]
        # Number of combinable drinks
        combinable_drinks = item_count["Café"] + item_count["Infusión"]
        # If there is at least the same amount of coffes as combinable food items
        if item_count["Café"] >= food_count:
            # The new number of coffes is recounted, and the number of each combinable food is converted into the apropriate breakfast combo
            item_association["Café"] = item_count["Café"] - food_count
            item_association["Desayuno + Café (tomate)"] = item_count["Barrita tomate"]
            item_association["Desayuno + Café (aceite)"] = item_count["Barrita aceite"]
            item_association["Desayuno + Café (napolitana)"] = item_count["Napolitana"]
            item_association["Desayuno + Café (croissant)"] = item_count["Croissant"]
            item_association["Infusión"] = item_count["Infusión"]

            # The price that each user has to pay is computed
            for user in users:
                user_name = user[0]
                user_price = user[1]
                if user_name in variable_users:
                    user_price = user_price[1]

                user_association[user_name] = user_price if user_name not in user_association else user_price + user_association[user_name]

        # If there is at least the same amount of coffes&teas as combinable food items
        elif combinable_drinks >= food_count:
            original_tea_count = item_count["Infusión"]
            # The new number of coffes is set to 0, and the number of each combinable food is converted into the apropriate breakfast combo
            item_association["Café"] = 0
            item_association["Desayuno + Café (tomate)"] = item_count["Barrita tomate"]
            item_association["Desayuno + Café (aceite)"] = item_count["Barrita aceite"]
            item_association["Desayuno + Café (napolitana)"] = item_count["Napolitana"]
            item_association["Desayuno + Café (croissant)"] = item_count["Croissant"]

            df_diff = combinable_drinks - food_count

            # The new number of teas is computed
            if df_diff == 0:
                item_association["Infusión"] = 0
            else:
                food_left = food_count - item_count["Café"]
                item_association["Infusión"] = item_count["Infusión"] - food_left

            # The price that each user has to pay is computed
            for user in users:
                user_name = user[0]
                user_price = user[1]
                if user_name in variable_users and user_name in drinker:
                    user_price = user_price[1]
                elif user_name in variable_users and user_name not in drinker:
                    not_drinkers = len(variable_users) - len(drinker)
                    tea_combos = original_tea_count - item_association["Infusión"]
                    user_price = user_price[1] + ((0.3 * tea_combos) / not_drinkers)

                user_association[user_name] = user_price if user_name not in user_association else user_price + user_association[user_name]
        else:
            st.write("This use case is out of scope. Good luck figuring this ticket out for yourselves. 😊")
            st.write("[Click here for emotional support](https://goatse.ru/)")

        item_association["Colacao"] = item_count["Colacao"]
        item_association["Yogurt"] = item_count["Yogurt"]
        item_association["Tortilla"] = item_count["Tortilla"]
        item_association["Palmera"] = item_count["Palmera"]

        # Create a DataFrame to display the ticket
        bar_selection = pd.DataFrame.from_dict(bar_count_dict, orient="index", columns=["Amount"])
        ticket_df = pd.DataFrame.from_dict(item_association, orient="index", columns=["Amount"])
        debts_ticket = pd.DataFrame.from_dict(user_association, orient="index", columns=["Spent"])

        # Format prices to show only 2 decimals
        debts_ticket["Spent"] = debts_ticket["Spent"].apply(lambda x: f"{x:.2f}")

        # Change indexes
        bar_selection = bar_selection.reset_index()
        ticket_df = ticket_df.reset_index()
        debts_ticket = debts_ticket.reset_index()

        # Rename the columns for clarity
        bar_selection.columns = ["Item", "Amount"]
        ticket_df.columns = ["Item", "Amount"]
        debts_ticket.columns = ["Name", "Spent"]

        # Filter rows to exclude zero amounts
        filtered_bar = bar_selection[bar_selection.index != "Nada"]
        filtered_machine = ticket_df[ticket_df["Amount"] > 0]

        st.subheader("Items to ask at the bar")
        st.dataframe(filtered_bar, hide_index=True, use_container_width=True)

        st.subheader("Paying Ticket")
        st.dataframe(filtered_machine, hide_index=True, use_container_width=True)

        st.subheader("Settle Up Ticket")
        st.dataframe(debts_ticket, hide_index=True, use_container_width=True)

        # Calculate and display the total price
        total_price = sum([float(price) for price in debts_ticket["Spent"]])
        st.write(f"**Total Price:** {total_price:.2f} €")

        # Save tickets to files
        filtered_bar.to_csv(bar_file, index=False)
        filtered_machine.to_csv(machine_file, index=False)
        debts_ticket.to_csv(debts_file, index=False)

        # Set ticket_generated to True in session state
        st.session_state.ticket_generated = True

    # Only show the "Submit Summary to History" button if a ticket is generated
    if st.session_state.ticket_generated:
        # Display warning
        st.warning("Warning: This will delete the current selection", icon="⚠️")

        if st.button("Close Poll", type="primary"):
            timestamp = save_summary_to_history(history_dir, selections_file, bar_file, machine_file, debts_file)
            st.success(f"Poll saved to history at {timestamp}")
            st.session_state.history = load_history(history_dir, selections_file, bar_file, machine_file, debts_file)

            # Clear local current selections
            if os.path.exists(selections_file):
                os.remove(selections_file)

                # Create an empty CSV to replace the deleted one
                pd.DataFrame(columns=["Name", "Drinks", "Food"]).to_csv(selections_file, index=False)

            # Reset session state for current selections and ticket generation status
            st.session_state.current_selections = []
            st.session_state.ticket_generated = False

            # Reload the current selections to show an empty table
            current_df = pd.DataFrame(columns=["Name", "Drinks", "Food"])
            st.dataframe(current_df, hide_index=True, use_container_width=True)


def history(history_dir, selections_file, bar_file, machine_file, debts_file):
    st.title("📜History📜")

    # Load history if it's not already loaded
    st.session_state.history = load_history(history_dir, selections_file, bar_file, machine_file, debts_file)

    # Sort history by the Date key in descending order
    st.session_state.history = sorted(st.session_state.history, key=lambda x: datetime.strptime(x["Date"], "%Y-%m-%d_%H-%M-%S"), reverse=True)

    if st.session_state.history:
        # Display history in reverse chronological order
        for record in st.session_state.history:
            # Format the date for display
            formatted_date = format_date(record["Date"])
            with st.expander(f"{formatted_date}"):
                st.markdown("#### Selections")
                st.dataframe(record["Selection"], hide_index=True, use_container_width=True)
                st.markdown("#### Bar")
                st.dataframe(record["Bar"], hide_index=True, use_container_width=True)
                st.markdown("#### Machine")
                st.dataframe(record["Machine"], hide_index=True, use_container_width=True)
                st.markdown("#### Debts")
                st.dataframe(record["Debts"], hide_index=True, use_container_width=True)

    else:
        st.write("No history records found.")


def settle(history_dir, debts_file):
    st.title("💲Settle💲")

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
                else:
                    st.subheader("No eligible person found to pay for coffees today")

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
