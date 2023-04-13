import json
import uuid
import re


def load_file(file_path):
    with open(file_path, 'r') as f:
        return f.read()


def save_file(content, file_path):
    with open(file_path, 'w') as f:
        f.write(content)


def update_config(config, upstream_uuid, bridge_uuid, outbound_domain):
    config = re.sub(r'<UPSTREAM_UUID>', upstream_uuid, config)
    config = re.sub(r'<BRIDGE_UUID>', bridge_uuid, config)
    config = re.sub(r'<OUTBOUND_DOMAIN>', outbound_domain, config)
    return config


def update_caddyfile(caddyfile, domain):
    return re.sub(r'<EXAMPLE.COM>', domain, caddyfile)


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


def prompt_domain():
    while True:
        domain = input(
            "Please enter the domain to be used in the Caddyfile (e.g., example.com): ").strip()
        if domain:
            return domain
        else:
            print("Empty input. Please provide a valid domain.")


def update_config_and_caddyfile(config_path, caddyfile_path):
    config = load_file(config_path)
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
    updated_config = update_config(
        config, upstream_uuid, bridge_uuid, outbound_domain)
    save_file(updated_config, config_path)

    caddyfile = load_file(caddyfile_path)
    domain = prompt_domain()
    updated_caddyfile = update_caddyfile(caddyfile, domain)
    save_file(updated_caddyfile, caddyfile_path)

    print("Configuration and Caddyfile updated successfully.")


if __name__ == "__main__":
    config_path = input(
        "Enter the path to the config.json or leave it empty to use the default (./xray/config/config.json): ").strip()
    if not config_path:
        config_path = "./xray/config/config.json"

    caddyfile_path = input(
        "Enter the path to the Caddyfile or leave it empty to use the default (./caddy/Caddyfile): ").strip()
    if not caddyfile_path:
        caddyfile_path = "./caddy/Caddyfile"

    update_config_and_caddyfile(config_path, caddyfile_path)
