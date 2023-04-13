import json
import uuid
import sys


def load_config(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)


def save_config(config, file_path):
    with open(file_path, 'w') as f:
        json.dump(config, f, indent=2)


def update_bridge_config(config, new_uuid, outbound_domain):
    config['inbounds'][0]['settings']['clients'][0]['id'] = new_uuid
    config['outbounds'][0]['settings']['vnext'][0]['address'] = outbound_domain
    return config


def prompt_uuid():
    while True:
        user_uuid = input(
            "Please enter a UUID or leave it empty to generate one: ").strip()
        if not user_uuid:
            return str(uuid.uuid4())
        try:
            uuid.UUID(user_uuid)
            return user_uuid
        except ValueError:
            print("Invalid UUID. Please try again or leave it empty to generate one.")


def prompt_outbound_domain():
    while True:
        outbound_domain = input(
            "Please enter the outbound domain (e.g., usnode1.example.com): ").strip()
        if outbound_domain:
            return outbound_domain
        else:
            print("Empty input. Please provide a valid outbound domain.")


def update_bridge_config_file(config_path):
    config = load_config(config_path)
    new_uuid = prompt_uuid()
    outbound_domain = prompt_outbound_domain()
    updated_config = update_bridge_config(config, new_uuid, outbound_domain)
    save_config(updated_config, config_path)
    print("Bridge configuration updated successfully.")


if __name__ == "__main__":
    config_path = input(
        "Enter the path to the bridge config.json or leave it empty to use the default (./xray/config/config.json): ").strip()
    if not config_path:
        config_path = "./xray/config/config.json"
    update_bridge_config_file(config_path)
