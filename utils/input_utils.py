import yaml


def load_users(users_file):
    with open(users_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["users"]

def save_users(users, users_file):
    sorted_users = sorted(users, key=lambda x: (x != "Invitado", x))
    with open(users_file, "w", encoding="utf-8") as f:
        yaml.dump({"users": sorted_users}, f, default_flow_style=False, allow_unicode=True)
