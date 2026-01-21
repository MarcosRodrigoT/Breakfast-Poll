import yaml
import pandas as pd


def load_csv(filename):
    return pd.read_csv(filename)


def save_csv(df, filename):
    df.to_csv(filename, index=False)


def load_yaml(yaml_file):
    with open(yaml_file, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return data


def save_yaml(data, yaml_file):
    with open(yaml_file, "w", encoding="utf-8") as file:
        yaml.safe_dump(data, file, allow_unicode=True)


def load_settleup(yaml_file):
    data = load_yaml(yaml_file)
    # rows = [{"Name": k, "Debt": v["settleup"]} for k, v in data.items()]
    rows = [{"Name": k} for k, v in data.items()]
    return pd.DataFrame(rows)


def load_descriptions(yaml_file):
    data = load_yaml(yaml_file)
    rows = [{"Name": k, "Description": v["description"]} for k, v in data.items()]
    return pd.DataFrame(rows)


def load_users(yaml_file):
    data = load_yaml(yaml_file)
    return list(data.keys())


def load_active_users(yaml_file):
    """Load only active users (not hidden) from the YAML file."""
    data = load_yaml(yaml_file)
    active_users = []
    for user, value in data.items():
        # Handle both old format (just a number) and new format (dict with status)
        if isinstance(value, dict):
            if value.get("status", "active") == "active":
                active_users.append(user)
        else:
            # Old format - all users are active by default
            active_users.append(user)
    return active_users


def load_hidden_users(yaml_file):
    """Load only hidden users from the YAML file."""
    data = load_yaml(yaml_file)
    hidden_users = []
    for user, value in data.items():
        if isinstance(value, dict) and value.get("status") == "hidden":
            hidden_users.append(user)
    return hidden_users


def toggle_user_status(yaml_file, user_name, new_status):
    """Toggle a user's status between 'active' and 'hidden'."""
    data = load_yaml(yaml_file)

    if user_name not in data:
        return False

    # Convert old format to new format if needed
    if not isinstance(data[user_name], dict):
        data[user_name] = {"debt": data[user_name], "status": "active"}

    # Update status
    data[user_name]["status"] = new_status

    save_yaml(data, yaml_file)
    return True


def save_users(users, users_file):
    sorted_users = sorted(users, key=lambda x: (x != "Invitado", x))
    with open(users_file, "w", encoding="utf-8") as f:
        yaml.dump({"users": sorted_users}, f, default_flow_style=False, allow_unicode=True)


def load_whopaid(whopaid_file):
    with open(whopaid_file, "r") as f:
        line = f.readline().strip()
        name, price = line.split(" - ")
        return name, float(price)


def save_whopaid(whopaid_file, whopaid, price):
    with open(whopaid_file, "w") as f:
        f.write(f"{whopaid} - {price}")


def add_user(yaml_file, new_user, new_debt, last_file):
    # Load existing data from the YAML file
    data = load_yaml(yaml_file)

    # Add user to last debts file
    result = add_user_to_last(last_file, new_user, new_debt)

    # Check if user already exists
    if new_user in data or not result:
        return False

    # Add the new user to the YAML file with new format
    data[new_user] = {"debt": 0, "status": "active"}

    # Save the updated data back to the YAML file
    save_yaml(data, yaml_file)
    return True


def add_user_to_last(last_file, new_user, new_debt):
    # Load the existing CSV into a DataFrame
    df = load_csv(last_file)

    # Check if the user already exists
    if new_user in df["Name"].values:
        return False

    # Add the new user
    new_row = pd.DataFrame({"Name": [new_user], "Debt": [new_debt]})
    df = pd.concat([df, new_row], ignore_index=True)

    # Sort by the Name column alphabetically
    df = df.sort_values(by="Name").reset_index(drop=True)

    # Save the updated DataFrame back to the CSV
    df.to_csv(last_file, index=False)
    return True
