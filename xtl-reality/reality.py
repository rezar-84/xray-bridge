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


def update_config_and_docker_compose_file(config_path, docker_compose_path):
    config = load_file(config_path)
    print(f"Original config: \n{config}\n")

    upstream_uuid = prompt_uuid("upstream")
    updated_config = update_config(config, upstream_uuid)
    print(f"Updated config: \n{updated_config}\n")

    save_file(updated_config, config_path)

    print("Configuration updated successfully.")


def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        sys.exit(1)


def generate_keys(container_name):
    print("Generating private and public keys...")
    run_command(
        f"docker exec {container_name} /bin/sh -c 'openssl genpkey -algorithm RSA -out /app/private_key.pem -pkeyopt rsa_keygen_bits:2048'")
    run_command(
        f"docker exec {container_name} /bin/sh -c 'openssl rsa -pubout -in /app/private_key.pem -out /app/public_key.pem'")
    print("Private and public keys generated successfully.")


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


def update_config(config, upstream_uuid, bridge_uuid, outbound_domain, private_key, public_key, short_id):
    config = re.sub(r'<UPSTREAM-UUID>', upstream_uuid, config)
    config = re.sub(r'<PRIVATE-KEY>', private_key, config)
    config = re.sub(r'<PUBLIC-KEY>', public_key, config)
    config = re.sub(r'<SHORT-ID>', short_id, config)
    return config


def main():
    config_path = input(
        "Enter the path to the config.json or leave it empty to use the default (./xray/config/config.json): ").strip()
    if not config_path:
        config_path = "./xray/config/config.json"

    docker_compose_path = input(
        "Enter the path to the docker-compose.yml or leave it empty to use the default (./docker-compose.yml): ").strip()
    if not docker_compose_path:
        docker_compose_path = "./docker-compose.yml"

    update_config_and_docker_compose_file(config_path, docker_compose_path)

    container_name = input(
        "Enter the name of the container where the keys will be generated: ").strip()

    if not container_name:
        print("Error: Container name is required.")
        sys.exit(1)

    generate_keys(container_name)
    # Generate X25519 keys
    x25519_keys = generate_x25519_keys()
    with open("x25519_keys.txt", "w") as keys_file:
        keys_file.write(x25519_keys)

    # Generate short ID
    short_id = generate_short_id()
    with open("short_id.txt", "w") as short_id_file:
        short_id_file.write(short_id)


if __name__ == "__main__":
    main()
