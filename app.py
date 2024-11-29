import streamlit as st
import pandas as pd
from datetime import datetime
import os
import subprocess
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter


# Local Directory Configuration
LOCAL_HISTORY_DIR = "history"
LOCAL_TEMP_FILE = "current_selections.csv"

# Initialize all required session state variables
if "users" not in st.session_state:
    st.session_state.users = []
if "current_selections" not in st.session_state:
    st.session_state.current_selections = []
if "step" not in st.session_state:
    st.session_state.step = 1
if "history" not in st.session_state:
    st.session_state.history = []


# Load temporary selections from the local file
def load_current_selections():
    if os.path.exists(LOCAL_TEMP_FILE):
        return pd.read_csv(LOCAL_TEMP_FILE)
    else:
        return pd.DataFrame(columns=["Name", "Drinks", "Food"])


# Save current user selections to the local CSV file without overwriting previous data
def save_current_selection_to_file(current_selections):
    current_selections["Drinks"] = current_selections["Drinks"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    current_selections["Food"] = current_selections["Food"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

    if os.path.exists(LOCAL_TEMP_FILE):
        existing_selections = pd.read_csv(LOCAL_TEMP_FILE)
        combined_selections = pd.concat([existing_selections, current_selections]).drop_duplicates()
    else:
        combined_selections = current_selections

    combined_selections.to_csv(LOCAL_TEMP_FILE, index=False)


# Load history from the local directory
def load_history():
    history = []
    if not os.path.exists(LOCAL_HISTORY_DIR):
        os.makedirs(LOCAL_HISTORY_DIR)

    history_files = [f for f in os.listdir(LOCAL_HISTORY_DIR) if f.endswith(".txt")]

    for file in history_files:
        file_path = os.path.join(LOCAL_HISTORY_DIR, file)
        summary_df = pd.read_csv(file_path)
        date = file.split(".txt")[0]
        history.append({"Date": date, "Summary": summary_df})
    return history


# Save the current summary to a text file in the local history directory
def save_summary_to_history():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    history_filename = os.path.join(LOCAL_HISTORY_DIR, f"{timestamp}.txt")

    if not os.path.exists(LOCAL_HISTORY_DIR):
        os.makedirs(LOCAL_HISTORY_DIR)

    if os.path.exists(LOCAL_TEMP_FILE):
        summary_df = pd.read_csv(LOCAL_TEMP_FILE)
        summary_df.to_csv(history_filename, index=False)

    return timestamp


# Load persistent history and temporary selections on app start
if "history" not in st.session_state:
    st.session_state.history = load_history()
    st.session_state.current_selections = load_current_selections().to_dict(orient="records")

# Sidebar for navigating through different views
menu = st.sidebar.selectbox("Select View", ["Poll", "Current", "History", "Graph"])


# Function to reset the current selections after submission
def reset_selections():
    st.session_state.users = []
    st.session_state.current_selections = []


# Poll view with four consecutive steps
if menu == "Poll":
    st.title("Breakfast Poll Application")

    # Step 1: User's Name
    st.header("Step 1: Enter your name")
    name_options = [
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
        "Victoria",
        "Narciso García",
        "Pablo Pérez",
        "Invitado",
    ]
    selected_user = st.radio("Select your name:", name_options)
    if st.button("Next", key="step1_next") and selected_user:
        st.session_state.users.append(selected_user)
        st.session_state.step = 2  # Set the next step to be visible

    # Show Step 2 only if Step 1 is completed
    if st.session_state.step >= 2:
        st.header("Step 2: Select your drink(s)")
        drinks_options = [
            "Café con leche",
            "Cortado",
            "Italiano",
            "Aguasusia",
            "Café sin lactosa",
            "Café con soja",
            "Descafeinado con leche",
            "Descafeinado con leche desnatada",
            "Aguasusia susia",
            "Colacao",
            "Té",
            "Manzanilla",
            "Nada",
        ]
        selected_drinks = st.radio("Choose your drinks:", drinks_options)

        if st.button("Next", key="step2_next") and selected_drinks:
            st.session_state.current_selections.append({"Name": st.session_state.users[-1], "Drinks": selected_drinks})
            st.session_state.step = 3  # Set the next step to be visible

    # Show Step 3 only if Step 2 is completed
    if st.session_state.step >= 3:
        st.header("Step 3: Select your food(s)")
        food_options = [
            "Barrita aceite",
            "Barrita tomate",
            "Napolitana de chocolate",
            "Croissant plancha",
            "Palmera chocolate",
            "Palmera chocolate blanco",
            "Tortilla",
            "Yogurt",
            "Nada",
        ]
        selected_food = st.radio("Choose your food:", food_options)

        if st.button("Save Selections", key="save_selections") and selected_food:
            st.session_state.current_selections[-1]["Food"] = selected_food
            df = pd.DataFrame(st.session_state.current_selections)
            save_current_selection_to_file(df)
            st.success(f"Selections saved for {st.session_state.users[-1]}!")
            st.session_state.step = 1  # Reset to step 1 for the next user

# History view to check past summaries
elif menu == "History":
    st.title("Breakfast Poll History")

    # Reload history if it's not already loaded
    if not st.session_state.history:
        st.session_state.history = load_history()

    if st.session_state.history:
        # Display history in reverse chronological order
        for record in reversed(st.session_state.history):
            st.subheader(f"Date: {record['Date']}")
            st.table(record["Summary"])
    else:
        st.write("No history records found.")

# "Current" view to display the current summary of all users' selections and generate ticket
elif menu == "Current":
    st.title("Current Selections of All Users")

    if st.button("Reload Selections"):
        # Reload the current selections from the local file
        st.session_state.current_selections = load_current_selections().to_dict(orient="records")
        st.success("Selections reloaded successfully!")

    # Load the current selections from the session state or from the file
    current_df = load_current_selections()
    st.table(current_df)

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

                user_association[user_name] = user_price

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

                user_association[user_name] = user_price
        else:
            raise NotImplementedError

        item_association["Colacaos"] = item_count["Colacao"]
        item_association["Yogurts"] = item_count["Yogurt"]
        item_association["Tortillas"] = item_count["Tortilla"]
        item_association["Palmeras"] = item_count["Palmera"]

        # Create a DataFrame to display the ticket
        bar_selection = pd.DataFrame.from_dict(bar_count_dict, orient="index", columns=["Amount"])
        ticket_df = pd.DataFrame.from_dict(item_association, orient="index", columns=["Amount"])
        settle_up_ticket = pd.DataFrame.from_dict(user_association, orient="index", columns=["Spent"])

        # Filter rows to exclude zero amounts
        filtered_bar = bar_selection[bar_selection.index != "Nada"]
        filtered_df = ticket_df[ticket_df["Amount"] > 0]

        # Format prices to show only 2 decimals
        settle_up_ticket["Spent"] = settle_up_ticket["Spent"].apply(lambda x: f"{x:.2f}")

        st.subheader("Items to ask at the bar")
        st.table(filtered_bar)

        st.subheader("Paying Ticket")
        st.table(filtered_df)

        st.subheader("Settle Up Ticket")
        st.table(settle_up_ticket)

        # Calculate and display the total price
        total_price = sum([float(price) for price in settle_up_ticket["Spent"]])
        st.write(f"**Total Price:** {total_price:.2f} €")

        # Set ticket_generated to True in session state
        st.session_state.ticket_generated = True

    # Only show the "Submit Summary to History" button if a ticket is generated
    if st.session_state.ticket_generated:
        if st.button("Submit Summary to History"):
            timestamp = save_summary_to_history()
            st.success(f"Summary saved to history at {timestamp}")
            st.session_state.history = load_history()

            # Clear local current selections
            if os.path.exists(LOCAL_TEMP_FILE):
                os.remove(LOCAL_TEMP_FILE)

                # Create an empty CSV to replace the deleted one
                pd.DataFrame(columns=["Name", "Drinks", "Food"]).to_csv(LOCAL_TEMP_FILE, index=False)

            # Reset session state for current selections and ticket generation status
            st.session_state.current_selections = []
            st.session_state.ticket_generated = False

            # Reload the current selections to show an empty table
            current_df = pd.DataFrame(columns=["Name", "Drinks", "Food"])
            st.table(current_df)

# History view to check past summaries
elif menu == "History":
    st.title("Breakfast Poll History")

    # Reload history if it's not already loaded
    if not st.session_state.history:
        st.session_state.history = load_history()

    if st.session_state.history:
        # Display history in reverse chronological order
        for record in reversed(st.session_state.history):
            st.subheader(f"Date: {record['Date']}")
            st.table(record["Summary"])
    else:
        st.write("No history records found.")

# Graph view to display a line chart of item selections over time
elif menu == "Graph":
    st.title("Breakfast Poll History - Graph View")

    # Load the history if not already loaded
    if not st.session_state.history:
        st.session_state.history = load_history()

    # Prepare data for plotting
    if st.session_state.history:
        history_data = []
        user_data = {}  # Store user-specific data

        for record in st.session_state.history:
            # Extract only the date part (YYYY-MM-DD) for display
            date = record["Date"].split("_")[0]  # Use only the YYYY-MM-DD portion of the date
            for index, row in record["Summary"].iterrows():
                user = row["Name"]
                for drink in row["Drinks"].split(", "):
                    history_data.append({"Date": date, "Item": drink, "Type": "Drink", "User": user})
                for food in row["Food"].split(", "):
                    history_data.append({"Date": date, "Item": food, "Type": "Food", "User": user})

                # Append user data for selection
                if user not in user_data:
                    user_data[user] = True  # Initialize all users as visible by default

        # Create a DataFrame from history data
        history_df = pd.DataFrame(history_data)

        # Count occurrences of each item per date
        item_counts = history_df.groupby(["Date", "Item", "Type", "User"]).size().reset_index(name="Count")

        # Separate items into Drinks and Food, and sort them alphabetically
        drinks = sorted(item_counts[item_counts["Type"] == "Drink"]["Item"].unique())
        foods = sorted(item_counts[item_counts["Type"] == "Food"]["Item"].unique())

        # Create a dictionary to store the checkbox values for each item
        item_visibility = {}

        # Create interactive checkboxes for Drinks, Food, and Users in the sidebar
        st.sidebar.header("Select Items to Display")

        # Drinks Section
        if drinks:
            st.sidebar.subheader("Drinks")
            for item in drinks:
                # Add a unique key to each checkbox to avoid duplicate widget IDs
                item_visibility[item] = st.sidebar.checkbox(item, value=True, key=f"checkbox_{item}_Drink")

        # Food Section
        if foods:
            st.sidebar.subheader("Food")
            for item in foods:
                # Add a unique key to each checkbox to avoid duplicate widget IDs
                item_visibility[item] = st.sidebar.checkbox(item, value=True, key=f"checkbox_{item}_Food")

        # User Section: Create a checkbox for each user to toggle their visibility
        st.sidebar.subheader("Users")
        for user in user_data.keys():
            user_data[user] = st.sidebar.checkbox(user, value=True, key=f"checkbox_user_{user}")

        # Filter the data based on selected items and users
        selected_items = [item for item, visible in item_visibility.items() if visible]
        selected_users = [user for user, visible in user_data.items() if visible]
        filtered_item_counts = item_counts[item_counts["Item"].isin(selected_items) & item_counts["User"].isin(selected_users)]

        # Check if there is data to display
        if not filtered_item_counts.empty:
            # Create a line plot for each selected item over time
            plt.figure(figsize=(12, 6))
            sns.lineplot(data=filtered_item_counts, x="Date", y="Count", hue="Item", marker="o")

            # Customize the y-axis to show only integer labels
            y_max = max(filtered_item_counts["Count"].max() + 1, 1)  # Set y_max to at least 1 to avoid errors
            plt.yticks(range(0, y_max))  # Show only integer labels on the y-axis

            # Customize the plot
            plt.xticks(rotation=45)
            plt.title("Item Selections Over Time")
            plt.xlabel("Date")
            plt.ylabel("Number of Selections")
            plt.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3)

            # Display the plot
            st.pyplot(plt.gcf())
        else:
            st.write("No data to display. Please select at least one user and one item.")
    else:
        st.write("No historical data available to plot.")


if __name__ == "__main__":
    # Define the port you want your app to run on
    PORT = 8500  # Replace with your preferred port number

    # Check if Streamlit is already running on the specified port
    try:
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(("127.0.0.1", PORT))
        s.close()
        print(f"Streamlit is already running on port {PORT}.")
    except (socket.error, ConnectionRefusedError):
        print(f"Launching Streamlit app on port {PORT}...")
        # Run Streamlit programmatically
        subprocess.run(["streamlit", "run", __file__, "--server.port", str(PORT)], check=True)
