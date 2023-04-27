#!/usr/bin/python3

import json
import uuid
import re
import os
import sys


def load_file(file_path):
    with open(file_path, 'r') as f:
        return f.read()


def save_file(content, file_path):
    with open(file_path, 'w') as f:
        f.write(content)


def update_config(config, upstream_uuid, bridge_uuid, outbound_domain):
    config = re.sub(r'<UPSTREAM-UUID>', upstream_uuid, config)
    config = re.sub(r'<BRIDGE-UUID>', bridge_uuid, config)
    config = re.sub(r'<OUTBOUND-DOMAIN>', outbound_domain, config)
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
    print(f"Original config: \n{config}\n")  # Add this print statement

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
    print(f"Updated config: \n{updated_config}\n")  # Add this print statement

    save_file(updated_config, config_path)

    caddyfile = load_file(caddyfile_path)
    domain = prompt_domain()
    updated_caddyfile = update_caddyfile(caddyfile, domain)
    save_file(updated_caddyfile, caddyfile_path)

    print("Configuration and Caddyfile updated successfully.")


def install_certbot():
    print("Installing Certbot...")
    if os.path.exists('/etc/debian_version'):
        run_command("sudo apt-get update")
        run_command("sudo apt-get install certbot python3-certbot-nginx")
    elif os.path.exists('/etc/redhat-release'):
        run_command("sudo yum install epel-release")
        run_command("sudo yum install certbot python3-certbot-nginx")
    else:
        print("Error: Unsupported distribution")
        sys.exit(1)


def obtain_certificate_certbot(domain):
    print(f"Obtaining SSL certificate for domain {domain}...")
    run_command(f"sudo certbot --nginx -d {domain}")


def install_acme_sh():
    print("Installing acme.sh...")
    run_command("curl https://get.acme.sh | sh")


def register_acme_sh_account():
    email = input(
        "Enter your email address for acme.sh account registration: ").strip()
    run_command(f"~/.acme.sh/acme.sh --register-account -m {email}")


def obtain_certificate_acme_sh(domain):
    print(f"Obtaining SSL certificate for domain {domain} using acme.sh...")
    run_command(
        f"sudo ~/.acme.sh/acme.sh --issue -d {domain} --standalone --debug -k ec-256")


def install_certificate_acme_sh(domain, caddyfile_path):
    fullchain_path = os.path.join(os.path.dirname(caddyfile_path), "xray.crt")
    key_path = os.path.join(os.path.dirname(caddyfile_path), "xray.key")
    run_command(
        f"sudo ~/.acme.sh/acme.sh --installcert -d {domain} --fullchainpath {fullchain_path} --keypath {key_path}")


def update_docker_compose_file(use_caddy):
    docker_compose_file = './docker-compose.yml'
    content = load_file(docker_compose_file)

    if not use_caddy:
        content = re.sub(r'caddy:.*depends_on:.*- xray.*ports:.*- "80:80".*- "443:443".*volumes:.*- \./caddy/Caddyfile:/etc/caddy/Caddyfile.*- \./caddy/web/:/usr/share/caddy.*- \./caddy/data/:/data/caddy/.*- \./caddy/config/:/config/caddy', '', content, flags=re.DOTALL)

    save_file(content, docker_compose_file)
    print("Docker-compose file updated successfully.")


def main():
    config_path = input(
        "Enter the path to the config.json or leave it empty to use the default (./xray/config/config.json): ").strip()
    if not config_path:
        config_path = "./xray/config/config.json"

    caddyfile_path = input(
        "Enter the path to the Caddyfile or leave it empty to use the default (./caddy/Caddyfile): ").strip()
    if not caddyfile_path:
        caddyfile_path = "./caddy/Caddyfile"

    update_config_and_caddyfile(config_path, caddyfile_path)

    use_caddy = input("Do you want to use Caddy? (yes/no): ").strip().lower()
    if use_caddy == 'yes':
        use_caddy = True
    else:
        use_caddy = False

    update_docker_compose_file(use_caddy)

    if use_caddy:
        install_certs = input(
            "Do you want to install SSL certificates? (yes/no): ").strip().lower()
        if install_certs == 'yes':
            domain = prompt_domain()

            cert_tool = input(
                "Choose the certificate tool to use (certbot/acme.sh): ").strip().lower()
            if cert_tool == 'certbot':
                install_certbot()
                obtain_certificate_certbot(domain)
            elif cert_tool == 'acme.sh':
                install_acme_sh()
                register_acme_sh_account()
                obtain_certificate_acme_sh(domain)
                install_certificate_acme_sh(domain, caddyfile_path)
            else:
                print("Error: Invalid certificate tool choice")
                sys.exit(1)

            print("Certificates have been installed and configured successfully.")
        else:
            print("Certificates installation skipped.")
    else:
        print("Caddy and certificate installation skipped.")


if __name__ == "__main__":
    main()
