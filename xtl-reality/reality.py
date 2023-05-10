#!/usr/bin/python3

import json
import uuid
import re
import os
import sys
import subprocess


def load_file(file_path):
    with open(file_path, 'r') as f:
        return f.read()


def save_file(content, file_path):
    with open(file_path, 'w') as f:
        f.write(content)


def update_config(config, upstream_uuid, bridge_uuid, outbound_domain, private_key, public_key, short_id):
    config = re.sub(r'<UPSTREAM-UUID>', upstream_uuid, config)
    config = re.sub(r'<BRIDGE-UUID>', bridge_uuid, config)
    config = re.sub(r'<OUTBOUND-DOMAIN>', outbound_domain, config)
    config = re.sub(r'<PRIVATE-KEY>', private_key, config)
    config = re.sub(r'<PUBLIC-KEY>', public_key, config)
    config = re.sub(r'<SHORT-ID>', short_id, config)
    return config


def prompt_uuid(label):
    while True:
        user_uuid = input(
            f"Please enter a UUID for {label} or leave it empty to generate one: ").strip()
        if not user_uuid:
            generated_uuid = str(uuid.uuid4())
            with open(f"{label}_generated_uuid.txt", "w") as uuid_file:
                uuid_file.write(generated_uuid)
            print(f"Generated UUID for {label}: {generated_uuid}")
            return generated_uuid
        try:
            uuid.UUID(user_uuid)
            return user_uuid
        except ValueError:
            print(
                f"Invalid UUID for {label}. Please try again or leave it empty to generate one.")


def prompt_outbound_domain():
    while True:
        outbound_domain = input(
            "Please enter the outbound domain (e.g., usnode1.example.com): ").strip()
        if outbound_domain:
            return outbound_domain
        else:
            print("Empty input. Please provide a valid outbound domain.")


def update_config_file(config_path, upstream_uuid, bridge_uuid, outbound_domain, private_key, public_key, short_id):
    config = load_file(config_path)
    print(f"Original config: \n{config}\n")

    updated_config = update_config(
        config, upstream_uuid, bridge_uuid, outbound_domain, private_key, public_key, short_id)
    print(f"Updated config: \n{updated_config}\n")

    save_file(updated_config, config_path)

    print("Configuration updated successfully.")


def generate_x25519_keys():
    result = subprocess.run(
        "docker exec gen_keys /usr/bin/xray x25519", shell=True, capture_output=True, text=True)
    output = result.stdout.strip()
    print(f"Generated X25519 keys:\n{output}")
    return output


def generate_short_id():
    result = subprocess.run(
        "openssl rand -hex 8", shell=True, capture_output=True, text=True)
    short_id = result.stdout.strip()
    print(f"Generated short ID: {short_id}")
    return short_id


def main():
    config_path = input(
        "Enter the path to the config.json or leave it empty to use the default (./xray/config/config.json): ").strip()
    if not config_path:
        config_path = "./xray/config/config.json"

    use_same_uuid = input(
        "Do you want to use the same UUID for both bridge and upstream? (y/n): ").strip().lower()

    if use_same_uuid == 'y':
        common_uuid = prompt_uuid("common")
        upstream_uuid = common_uuid
        bridge_uuid = common_uuid
    else:
        upstream_uuid = prompt_uuid("upstream")
        bridge_uuid = prompt_uuid("bridge")

    outbound_domain = prompt_outbound_domain()

    # Generate X25519 keys and extract private and public keys
    x25519_output = generate_x25519_keys()
    private_key = re.search(r'Private key: (\S+)', x25519_output).group(1)
    public_key = re.search(r'Public key: (\S+)', x25519_output).group(1)

    # Generate short ID
    short_id = generate_short_id()

    # Update config file with generated values
    update_config_file(
        config_path, upstream_uuid, bridge_uuid, outbound_domain, private_key, public_key, short_id)

    print("Script completed successfully.")


if __name__ == "__main__":
    main()
