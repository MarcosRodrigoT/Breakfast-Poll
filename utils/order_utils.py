import os
import pandas as pd
import streamlit as st
import yaml
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


def load_pricing_config(config_file="inputs/pricing.yaml"):
    """Load pricing configuration from YAML file."""
    with open(config_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_item_prices_dict(config):
    """Build item_prices dictionary from config: {item_name: (price, category)}."""
    item_prices = {}
    for item_name, item_data in config["items"].items():
        item_prices[item_name] = (item_data["price"], item_data["category"])
    return item_prices


# Complex ticket logic with combo optimization
def ticket_logic(current_df):
    # Load pricing from YAML configuration
    config = load_pricing_config()
    item_prices = build_item_prices_dict(config)

    # Define combinable items (items that can be part of breakfast combos)
    combinable = [
        "Café",
        "Infusión",
        "Barrita aceite",
        "Barrita tomate",
        "Napolitana de chocolate",
        "Croissant plancha",
    ]

    # Initialize tracking lists
    users = []  # List of (user_name, price) tuples
    drinks = []  # All drinks ordered (for bar ticket)
    foods = []  # All foods ordered (for bar ticket)
    variable_users = []  # Users whose final price depends on combo optimization
    drinker = []  # Users with drinks whose price might vary based on combos
    combo_users = []  # Users who ordered a perfect combo
    infusion_drinker = []  # Users who ordered infusion + combinable food

    # Process each user's order
    for _, row in current_df.iterrows():
        user_name = row["Name"]
        user_drink = row["Drinks"]
        user_food = row["Food"]

        drinks.append(user_drink)
        foods.append(user_food)

        # Calculate user price based on their selection
        user_price = calculate_user_price(
            user_name, user_drink, user_food, item_prices, combinable,
            variable_users, drinker, combo_users, infusion_drinker
        )

        users.append((user_name, user_price))

    # Generate bar ticket (what to order at cafeteria)
    bar_ticket = generate_bar_ticket(drinks, foods)

    # Count items by category for combo optimization
    drinks_by_category = [item_prices[x][1] for x in drinks]
    foods_by_category = [item_prices[x][1] for x in foods]

    item_count = count_items_by_category(drinks_by_category, foods_by_category)

    # Optimize combo assignments and calculate final user prices
    user_association = optimize_combos_and_calculate_prices(
        users, item_count, variable_users, drinker, infusion_drinker
    )

    # Generate machine ticket (optimized for payment)
    machine_ticket = generate_machine_ticket(item_count)

    # Generate debts ticket (how much each person owes)
    debts_ticket = generate_debts_ticket(user_association)

    return bar_ticket, machine_ticket, debts_ticket


def calculate_user_price(user_name, user_drink, user_food, item_prices, combinable,
                          variable_users, drinker, combo_users, infusion_drinker):
    """
    Calculate the price for a single user's order.
    Returns either a single price or a tuple of prices for variable pricing scenarios.
    """
    drink_price, drink_category = item_prices.get(user_drink, (0, "Nada"))
    food_price, food_category = item_prices.get(user_food, (0, "Nada"))

    # Case 1: Only drink ordered
    if user_drink != "Nada" and user_food == "Nada":
        return drink_price

    # Case 2: Only food ordered
    if user_drink == "Nada" and user_food != "Nada":
        if user_food in combinable:
            # Food might be paired with someone else's drink in a combo
            # Tuple format: (base_price, price_if_paired_with_coffee, price_if_paired_with_infusion)
            if food_category in ["Barrita aceite", "Napolitana"]:
                user_price = (food_price, 0.65, 0.95)  # 1.85 combo - 1.20 coffee = 0.65
                variable_users.append(user_name)
            elif food_category in ["Barrita tomate", "Croissant"]:
                user_price = (food_price, 1.3, 1.6)  # 2.50 combo - 1.20 coffee = 1.30
                variable_users.append(user_name)
            else:
                user_price = food_price
        else:
            user_price = food_price
        return user_price

    # Case 3: Both drink and food ordered
    if user_drink != "Nada" and user_food != "Nada":
        # Check if food can be part of a combo
        if user_food in combinable:
            # Check if drink can be part of a combo
            if drink_category in combinable:
                # Both are combinable - perfect combo!
                if drink_category == "Café":
                    # Coffee combo
                    if food_category in ["Barrita aceite", "Napolitana"]:
                        user_price = 1.85
                        combo_users.append((user_name, user_drink, user_food))
                    elif food_category in ["Barrita tomate", "Croissant"]:
                        user_price = 2.5
                        combo_users.append((user_name, user_drink, user_food))
                    else:
                        user_price = drink_price + food_price
                elif drink_category == "Infusión":
                    # Infusion combo (might get discount if enough coffees available)
                    # Tuple format: (regular_combo_price, discounted_price)
                    if food_category in ["Barrita aceite", "Napolitana"]:
                        user_price = (1.85, 1.55)
                        variable_users.append(user_name)
                        drinker.append(user_name)
                        infusion_drinker.append(user_name)
                        combo_users.append((user_name, user_drink, user_food))
                    elif food_category in ["Barrita tomate", "Croissant"]:
                        user_price = (2.5, 2.2)
                        variable_users.append(user_name)
                        drinker.append(user_name)
                        infusion_drinker.append(user_name)
                        combo_users.append((user_name, user_drink, user_food))
                    else:
                        user_price = drink_price + food_price
                else:
                    user_price = drink_price + food_price
            else:
                # Drink not combinable, but food is (e.g., Colacao + Barrita)
                # Food might be paired with someone else's coffee
                # Tuple format: (base_price, optimized_price_if_coffee_available)
                if food_category in ["Barrita aceite", "Napolitana"]:
                    user_price = (drink_price + food_price, 2.15)  # Colacao 1.50 + contribution 0.65
                    variable_users.append(user_name)
                    drinker.append(user_name)
                elif food_category in ["Barrita tomate", "Croissant"]:
                    user_price = (drink_price + food_price, 2.8)  # Colacao 1.50 + contribution 1.30
                    variable_users.append(user_name)
                    drinker.append(user_name)
                else:
                    user_price = drink_price + food_price
        else:
            # Food not combinable - simple addition
            user_price = drink_price + food_price

        return user_price

    # Case 4: Nothing ordered
    return 0.0


def count_items_by_category(drinks_by_category, foods_by_category):
    """Count how many items of each category were ordered."""
    return {
        "Café": len([x for x in drinks_by_category if x == "Café"]),
        "Colacao": len([x for x in drinks_by_category if x == "Colacao"]),
        "Infusión": len([x for x in drinks_by_category if x == "Infusión"]),
        "Barrita aceite": len([x for x in foods_by_category if x == "Barrita aceite"]),
        "Barrita tomate": len([x for x in foods_by_category if x == "Barrita tomate"]),
        "Napolitana": len([x for x in foods_by_category if x == "Napolitana"]),
        "Croissant": len([x for x in foods_by_category if x == "Croissant"]),
        "Palmera": len([x for x in foods_by_category if x == "Palmera"]),
        "Tortilla": len([x for x in foods_by_category if x == "Tortilla"]),
        "Yogurt": len([x for x in foods_by_category if x == "Yogurt"]),
    }


def optimize_combos_and_calculate_prices(users, item_count, variable_users, drinker, infusion_drinker):
    """
    Optimize combo assignments to minimize total cost and calculate final price for each user.
    This implements the complex logic of pairing drinks with foods to create combos.
    """
    user_association = {}

    # Count combinable items
    food_count = (
        item_count["Barrita aceite"] + item_count["Barrita tomate"] +
        item_count["Napolitana"] + item_count["Croissant"]
    )
    coffee_count = item_count["Café"]
    infusion_count = item_count["Infusión"]
    combinable_drinks = coffee_count + infusion_count

    # Scenario 1: Enough coffees to pair with all combinable foods
    if coffee_count >= food_count:
        for user_name, user_price in users:
            if user_name in variable_users:
                # Use optimized price (index 1 in tuple)
                user_association[user_name] = user_price[1]
            else:
                user_association[user_name] = user_price

    # Scenario 2: Need to use infusions for some combos
    elif combinable_drinks >= food_count:
        original_tea_count = infusion_count
        not_drinkers = len(variable_users) - len(drinker)

        # Calculate how many combos will use infusions instead of coffee
        food_left = food_count - coffee_count
        tea_combos = min(food_left, original_tea_count)

        # Calculate savings from using tea (0.90€) instead of coffee (1.20€) in combos
        # Savings = 0.30€ per tea combo, distributed fairly among relevant users
        tea_savings = 0.3 * tea_combos

        # Distribute the tea savings fairly
        for user_name, user_price in users:
            if not_drinkers > 0 and not_drinkers > tea_combos:
                # More non-drinkers than tea combos: distribute among non-drinkers
                if user_name in variable_users and user_name in drinker:
                    user_association[user_name] = user_price[1]
                elif user_name in variable_users and user_name not in drinker:
                    user_association[user_name] = user_price[1] + (tea_savings / not_drinkers)
                else:
                    user_association[user_name] = user_price
            elif not_drinkers == 0:
                # No non-drinkers: distribute among infusion drinkers
                if user_name in variable_users and user_name in infusion_drinker:
                    user_association[user_name] = user_price[1] + (tea_savings / len(infusion_drinker))
                elif user_name in variable_users and user_name not in infusion_drinker:
                    user_association[user_name] = user_price[1]
                else:
                    user_association[user_name] = user_price
            elif not_drinkers > 0 and not_drinkers < tea_combos:
                # More tea combos than non-drinkers: distribute among all variable users
                if user_name in variable_users:
                    user_association[user_name] = user_price[1] + (tea_savings / len(variable_users))
                else:
                    user_association[user_name] = user_price
            else:
                user_association[user_name] = user_price if isinstance(user_price, float) else user_price[1]

    # Scenario 3: Not enough drinks for all combos (should rarely happen)
    else:
        st.write("This use case is out of scope. Good luck figuring this ticket out for yourselves. 😊")
        st.write("[Click here for emotional support](https://goatse.ru/)")
        # Fall back to base prices
        for user_name, user_price in users:
            user_association[user_name] = user_price if isinstance(user_price, float) else user_price[0]

    return user_association


def generate_bar_ticket(drinks, foods):
    """Generate bar ticket showing what items to order at the cafeteria."""
    bar_items = sorted(drinks) + sorted(foods)
    bar_count = Counter(bar_items)

    # Create DataFrame and filter out "Nada"
    bar_df = pd.DataFrame.from_dict(dict(bar_count), orient="index", columns=["Amount"])
    bar_df = bar_df.reset_index()
    bar_df.columns = ["Item", "Amount"]
    bar_df = bar_df[bar_df["Item"] != "Nada"]

    return bar_df


def generate_machine_ticket(item_count):
    """Generate machine ticket showing optimized combo items for payment."""
    item_association = {}

    # Calculate combo assignments
    food_count = (
        item_count["Barrita aceite"] + item_count["Barrita tomate"] +
        item_count["Napolitana"] + item_count["Croissant"]
    )
    coffee_count = item_count["Café"]
    infusion_count = item_count["Infusión"]
    combinable_drinks = coffee_count + infusion_count

    # Assign combos based on available drinks
    if coffee_count >= food_count:
        # All foods paired with coffee
        item_association["Café"] = coffee_count - food_count
        item_association["Infusión"] = infusion_count
    elif combinable_drinks >= food_count:
        # Some foods paired with infusions
        item_association["Café"] = 0
        food_left = food_count - coffee_count
        item_association["Infusión"] = infusion_count - food_left

    # Add combo items
    item_association["Desayuno + Café (tomate)"] = item_count["Barrita tomate"]
    item_association["Desayuno + Café (aceite)"] = item_count["Barrita aceite"]
    item_association["Desayuno + Café (napolitana)"] = item_count["Napolitana"]
    item_association["Desayuno + Café (croissant)"] = item_count["Croissant"]

    # Add non-combinable items
    item_association["Colacao"] = item_count["Colacao"]
    item_association["Palmera"] = item_count["Palmera"]
    item_association["Tortilla"] = item_count["Tortilla"]
    item_association["Yogurt"] = item_count["Yogurt"]

    # Create DataFrame and filter zero amounts
    machine_df = pd.DataFrame.from_dict(item_association, orient="index", columns=["Amount"])
    machine_df = machine_df.reset_index()
    machine_df.columns = ["Item", "Amount"]
    machine_df = machine_df[machine_df["Amount"] > 0]

    return machine_df


def generate_debts_ticket(user_association):
    """Generate debts ticket showing how much each person owes."""
    debts_df = pd.DataFrame.from_dict(user_association, orient="index", columns=["Debt"])
    debts_df = debts_df.reset_index()
    debts_df.columns = ["Name", "Debt"]

    # Format prices to 2 decimals
    debts_df["Debt"] = debts_df["Debt"].apply(lambda x: f"{x:.2f}")

    return debts_df
