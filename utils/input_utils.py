import yaml


def load_users(users_file):
    with open(users_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["users"]