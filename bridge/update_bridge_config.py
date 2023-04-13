import json
import uuid
import sys
import re


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


def update_caddyfile(file_path, domain):
    with open(file_path, 'r') as f:
        content = f.read()
    content = re.sub(r'<EXAMPLE.COM>', domain, content)
    with open(file_path, 'w') as f:
        f.write(content)


def prompt_uuid():
    while True:
        user_uuid = input(
            "Please enter a UUID or leave it empty to generate one: ").strip()
        if not user_uuid:
            generated_uuid = str(uuid.uuid4())
            with open("generated_uuid.txt", "w") as uuid_file:
                uuid_file.write(generated_uuid)
            print(f"Generated UUID: {generated_uuid}")
            return generated_uuid
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


def update_bridge_config_file(config_path, caddyfile_path):
    config = load_config(config_path)
    new_uuid = prompt_uuid()
    outbound_domain = prompt_outbound_domain()
    updated_config = update_bridge_config(config, new_uuid, outbound_domain)
    save_config(updated_config, config_path)
    update_caddyfile(caddyfile_path, outbound_domain)
    print("Bridge configuration updated successfully.")


if __name__ == "__main__":
    config_path = input(
        "Enter the path to the bridge config.json or leave it empty to use the default (./xray/config/config.json): ").strip()
    if not config_path:
        config_path = "./xray/config/config.json"

    caddyfile_path = input(
        "Enter the path to the Caddyfile or leave it empty to use the default (./caddy/Caddyfile): ").strip()
    if not caddyfile_path:
        caddyfile_path = "./caddy/Caddyfile"

    update_bridge_config_file(config_path, caddyfile_path)
