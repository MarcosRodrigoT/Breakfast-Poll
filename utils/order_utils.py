import os
import pandas as pd
import streamlit as st
from collections import Counter


# Load temporary order from the local file
def load_order(order_file):
    if os.path.exists(order_file):
        return pd.read_csv(order_file)
    else:
        return pd.DataFrame(columns=["Name", "Drinks", "Food"])


# Save current order to the local CSV file without overwriting previous data
def save_order(current_order, order_file, combine=True):
    current_order["Drinks"] = current_order["Drinks"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    current_order["Food"] = current_order["Food"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

    if os.path.exists(order_file) and combine:
        existing_order = pd.read_csv(order_file)
        combined_order = pd.concat([existing_order, current_order]).drop_duplicates()
    else:
        combined_order = current_order

    combined_order.to_csv(order_file, index=False)


# Complex ticke logic
def ticket_logic(current_df):
    
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
        "Té con leche": (1.2, "Café"),
        "Colacao": (1.5, "Colacao"),
        "Té": (0.9, "Infusión"),
        "Manzanilla": (0.9, "Infusión"),
        "Barrita aceite": (1.85, "Barrita aceite"),
        "Barrita tomate": (2.5, "Barrita tomate"),
        "Napolitana de chocolate": (1.85, "Napolitana"),
        "Croissant plancha": (2.5, "Croissant"),
        "Palmera chocolate": (1.5, "Palmera"),
        "Palmera chocolate blanco": (1.5, "Palmera"),
        "Tortilla": (1.4, "Tortilla"),
        "Yogurt": (0.9, "Yogurt"),
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

    # Iterate over each user's selections
    users = []  # Users that have answer the poll
    drinks = []  # Drinks selected in the poll
    foods = []  # Foods selected in the poll
    variable_users = []  # Users whose price might change depending on combo conditions
    drinker = []  # Users that have gotten a drink and whose price might change depending on combo conditions
    combo_users = []  # Users that have gotten a combo option
    infusion_drinker = []  # Users that have gotten an infusion as a drink

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
                                    infusion_drinker.append(user_name)
                                    combo_users.append((user_name, user_drink, user_food))
                                # If chosen food belongs to the expensier breakfast combo
                                case "Barrita tomate" | "Croissant":
                                    user_price = (2.5, 2.2)
                                    variable_users.append(user_name)
                                    drinker.append(user_name)
                                    infusion_drinker.append(user_name)
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
        not_drinkers = len(variable_users) - len(drinker)

        # The new number of teas is computed
        if df_diff == 0:
            item_association["Infusión"] = 0
        else:
            food_left = food_count - item_count["Café"]
            item_association["Infusión"] = item_count["Infusión"] - food_left

        # Number of combos that have been made with an infusion
        tea_combos = original_tea_count - item_association["Infusión"]

        # The price that each user has to pay is computed
        for user in users:
            user_name = user[0]
            user_price = user[1]
            if not_drinkers > 0 and not_drinkers > tea_combos:
                if user_name in variable_users and user_name in drinker:
                    user_price = user_price[1]
                elif user_name in variable_users and user_name not in drinker:
                    user_price = user_price[1] + ((0.3*tea_combos)/not_drinkers)
            elif not_drinkers == 0:
                if user_name in variable_users and user_name in infusion_drinker:
                    user_price = user_price[1] + ((0.3*tea_combos)/len(infusion_drinker))
                elif user_name in variable_users and user_name not in infusion_drinker:
                    user_price = user_price[1]
            elif not_drinkers > 0 and not_drinkers < tea_combos:
                user_price = user_price[1] + ((0.3*tea_combos)/len(variable_users))

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
    debts_ticket = pd.DataFrame.from_dict(user_association, orient="index", columns=["Debt"])

    # Format prices to show only 2 decimals
    debts_ticket["Debt"] = debts_ticket["Debt"].apply(lambda x: f"{x:.2f}")

    # Change indexes
    bar_selection = bar_selection.reset_index()
    ticket_df = ticket_df.reset_index()
    debts_ticket = debts_ticket.reset_index()

    # Rename the columns for clarity
    bar_selection.columns = ["Item", "Amount"]
    ticket_df.columns = ["Item", "Amount"]
    debts_ticket.columns = ["Name", "Debt"]

    # Filter rows to exclude zero amounts
    filtered_bar = bar_selection[bar_selection["Item"] != "Nada"]
    filtered_machine = ticket_df[ticket_df["Amount"] > 0]
    
    return filtered_bar, filtered_machine, debts_ticket
