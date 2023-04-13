import json
import uuid
import sys


def load_config(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)


def save_config(config, file_path):
    with open(file_path, 'w') as f:
        json.dump(config, f, indent=2)


def update_upstream_config(config, new_uuid):
    config['inbounds'][0]['settings']['clients'][0]['id'] = new_uuid
    return config


def prompt_uuid():
    while True:
        user_uuid = input(
            "Please enter the UUID used in the bridge server config: ").strip()
        if not user_uuid:
            print("Empty input. Please provide a valid UUID.")
        else:
            try:
                uuid.UUID(user_uuid)
                return user_uuid
            except ValueError:
                print("Invalid UUID. Please try again.")


def update_upstream_config_file(config_path):
    config = load_config(config_path)
    new_uuid = prompt_uuid()
    updated_config = update_upstream_config(config, new_uuid)
    save_config(updated_config, config_path)
    print("Upstream configuration updated successfully.")


if __name__ == "__main__":
    config_path = input(
        "Enter the path to the upstream config.json or leave it empty to use the default (./config/config.json): ").strip()
    if not config_path:
        config_path = "./config/config.json"
    update_upstream_config_file(config_path)
