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


def get_item_info(item_name, config):
    """Get price and category for an item."""
    item = config["items"].get(item_name, {})
    return item.get("price", 0), item.get("category", "Unknown")


def find_combo(drink_category, food_category, config):
    """Find matching combo for drink and food categories."""
    for combo in config["combos"]:
        if drink_category in combo["drink_categories"] and food_category in combo["food_categories"]:
            return combo
    return None


def is_combinable_food(food_category):
    """Check if a food category can be combined."""
    return food_category in ["Barrita aceite", "Barrita tomate", "Napolitana", "Croissant"]


def is_combinable_drink(drink_category):
    """Check if a drink category can be combined."""
    return drink_category in ["Café", "Infusión"]


# Refactored ticket logic
def ticket_logic(current_df):
    """
    Calculate ticket breakdown with combo pricing.
    Now uses externalized pricing configuration from pricing.yaml
    """
    # Load pricing configuration
    config = load_pricing_config()

    # Data structures for processing
    users = []  # (user_name, price) tuples
    drinks_raw = []  # Original drink names for bar ticket
    foods_raw = []  # Original food names for bar ticket

    # Track users with variable pricing (for combo optimization)
    variable_users = {}  # {user_name: price_options}
    infusion_combo_users = []  # Users who ordered infusion + combinable food
    food_only_users = []  # Users who only ordered combinable food

    # Count items by category
    category_counts = Counter()

    # Process each user's order
    for _, row in current_df.iterrows():
        user_name = row["Name"]
        user_drink = row["Drinks"]
        user_food = row["Food"]

        drinks_raw.append(user_drink)
        foods_raw.append(user_food)

        drink_price, drink_cat = get_item_info(user_drink, config)
        food_price, food_cat = get_item_info(user_food, config)

        # Count categories (excluding "Nada")
        if drink_cat != "Nada":
            category_counts[drink_cat] += 1
        if food_cat != "Nada":
            category_counts[food_cat] += 1

        # Calculate user price based on their selection
        user_price = calculate_user_price(
            user_name, user_drink, user_food,
            drink_price, drink_cat, food_price, food_cat,
            config, variable_users, infusion_combo_users, food_only_users
        )

        users.append((user_name, user_price))

    # Optimize combo assignments and calculate final prices
    user_debts = optimize_combo_pricing(
        users, category_counts, variable_users,
        infusion_combo_users, food_only_users
    )

    # Generate tickets
    bar_ticket = generate_bar_ticket(drinks_raw, foods_raw)
    machine_ticket = generate_machine_ticket(category_counts, config)
    debts_ticket = generate_debts_ticket(user_debts)

    return bar_ticket, machine_ticket, debts_ticket


def calculate_user_price(user_name, drink, food, drink_price, drink_cat,
                         food_price, food_cat, config, variable_users,
                         infusion_combo_users, food_only_users):
    """Calculate price for a single user's order."""

    # Case 1: Only drink
    if drink != "Nada" and food == "Nada":
        return drink_price

    # Case 2: Only food
    if drink == "Nada" and food != "Nada":
        if is_combinable_food(food_cat):
            # Food can potentially be part of a combo
            combo = find_combo("Café", food_cat, config)
            if combo:
                # Store multiple price options for later optimization
                base_price = food_price
                combo_contribution = combo["price"] - 1.20  # Coffee price
                infusion_contribution = combo["price"] - 0.90  # Infusion price
                variable_users[user_name] = (base_price, combo_contribution, infusion_contribution)
                food_only_users.append(user_name)
                return base_price  # Default to base price
        return food_price

    # Case 3: Both drink and food
    if drink != "Nada" and food != "Nada":
        # Try to find a combo
        combo = find_combo(drink_cat, food_cat, config)

        if combo:
            # Perfect combo match
            if drink_cat == "Café":
                return combo["price"]
            elif drink_cat == "Infusión":
                # Infusion combos may get discount if enough coffees available
                regular_price = combo["price"]
                discount_price = combo.get("discount_price", regular_price)
                variable_users[user_name] = (regular_price, discount_price)
                infusion_combo_users.append(user_name)
                return regular_price  # Default to regular price
        else:
            # Check if food is combinable but drink isn't
            if is_combinable_food(food_cat) and not is_combinable_drink(drink_cat):
                # Non-combinable drink + combinable food
                # Could potentially use the food in someone else's combo
                base_price = drink_price + food_price
                combo_coffee = find_combo("Café", food_cat, config)
                if combo_coffee:
                    combo_contribution = combo_coffee["price"]
                    variable_users[user_name] = (base_price, combo_contribution)
                    food_only_users.append(user_name)
                return base_price

            # No combo possible
            return drink_price + food_price

    # Case 4: Nothing ordered
    return 0.0


def optimize_combo_pricing(users, category_counts, variable_users,
                           infusion_combo_users, food_only_users):
    """Optimize combo assignments to minimize total cost."""

    user_debts = {}

    # Count combinable items
    combinable_foods = (
        category_counts.get("Barrita aceite", 0) +
        category_counts.get("Barrita tomate", 0) +
        category_counts.get("Napolitana", 0) +
        category_counts.get("Croissant", 0)
    )
    coffee_count = category_counts.get("Café", 0)
    infusion_count = category_counts.get("Infusión", 0)
    combinable_drinks = coffee_count + infusion_count

    # Scenario 1: Enough coffees for all combinable foods
    if coffee_count >= combinable_foods:
        for user_name, price in users:
            if user_name in variable_users:
                # Use the optimized price (index 1)
                user_debts[user_name] = variable_users[user_name][1]
            else:
                user_debts[user_name] = price

    # Scenario 2: Need to use infusions for some combos
    elif combinable_drinks >= combinable_foods:
        tea_combos = combinable_foods - coffee_count
        tea_savings = tea_combos * 0.30  # 0.30€ saved per tea combo (0.90 instead of 1.20)

        # Distribute savings
        if len(infusion_combo_users) > 0:
            # Distribute among infusion users
            savings_per_user = tea_savings / len(infusion_combo_users)
            for user_name, price in users:
                if user_name in infusion_combo_users and user_name in variable_users:
                    discount_price = variable_users[user_name][1]
                    user_debts[user_name] = discount_price + savings_per_user
                elif user_name in variable_users:
                    user_debts[user_name] = variable_users[user_name][1]
                else:
                    user_debts[user_name] = price
        else:
            # Distribute among food-only users
            if len(food_only_users) > 0:
                savings_per_user = tea_savings / len(food_only_users)
                for user_name, price in users:
                    if user_name in food_only_users and user_name in variable_users:
                        user_debts[user_name] = variable_users[user_name][1] + savings_per_user
                    elif user_name in variable_users:
                        user_debts[user_name] = variable_users[user_name][1]
                    else:
                        user_debts[user_name] = price
            else:
                # Distribute among all variable users
                if len(variable_users) > 0:
                    savings_per_user = tea_savings / len(variable_users)
                    for user_name, price in users:
                        if user_name in variable_users:
                            user_debts[user_name] = variable_users[user_name][1] + savings_per_user
                        else:
                            user_debts[user_name] = price
                else:
                    for user_name, price in users:
                        user_debts[user_name] = price

    # Scenario 3: Not enough drinks for combos (edge case)
    else:
        st.write("This use case is out of scope. Good luck figuring this ticket out for yourselves. 😊")
        st.write("[Click here for emotional support](https://goatse.ru/)")
        # Default to base prices
        for user_name, price in users:
            user_debts[user_name] = price

    return user_debts


def generate_bar_ticket(drinks, foods):
    """Generate bar ticket showing what to order at cafeteria."""
    items = [item for item in drinks + foods if item != "Nada"]
    item_counts = Counter(items)

    df = pd.DataFrame(list(item_counts.items()), columns=["Item", "Amount"])
    return df.sort_values("Item").reset_index(drop=True)


def generate_machine_ticket(category_counts, config):
    """Generate machine ticket showing optimized items for payment."""
    machine_items = {}

    # Calculate combo items
    combinable_foods = (
        category_counts.get("Barrita aceite", 0) +
        category_counts.get("Barrita tomate", 0) +
        category_counts.get("Napolitana", 0) +
        category_counts.get("Croissant", 0)
    )
    coffee_count = category_counts.get("Café", 0)
    combinable_drinks = coffee_count + category_counts.get("Infusión", 0)

    if coffee_count >= combinable_foods:
        # All foods become combos
        machine_items["Café"] = coffee_count - combinable_foods
        machine_items["Infusión"] = category_counts.get("Infusión", 0)
    elif combinable_drinks >= combinable_foods:
        # Use all drinks for combos
        machine_items["Café"] = 0
        foods_left = combinable_foods - coffee_count
        machine_items["Infusión"] = category_counts.get("Infusión", 0) - foods_left

    # Add combo items using machine display names
    display = config.get("machine_display", {})
    for food_cat in ["Barrita aceite", "Barrita tomate", "Napolitana", "Croissant"]:
        count = category_counts.get(food_cat, 0)
        if count > 0:
            display_name = display.get(food_cat, f"Desayuno + Café ({food_cat.lower()})")
            machine_items[display_name] = count

    # Add non-combinable items
    for cat in ["Colacao", "Palmera", "Tortilla", "Yogurt"]:
        count = category_counts.get(cat, 0)
        if count > 0:
            machine_items[cat] = count

    # Filter out zero amounts
    machine_items = {k: v for k, v in machine_items.items() if v > 0}

    df = pd.DataFrame(list(machine_items.items()), columns=["Item", "Amount"])
    return df.reset_index(drop=True)


def generate_debts_ticket(user_debts):
    """Generate debts ticket showing cost per person."""
    df = pd.DataFrame(list(user_debts.items()), columns=["Name", "Debt"])
    df["Debt"] = df["Debt"].apply(lambda x: f"{x:.2f}")
    return df.reset_index(drop=True)
