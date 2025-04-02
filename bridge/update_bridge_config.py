#!/usr/bin/python3

import json
import uuid
import re
import os
import sys
import subprocess

def print_banner():
    banner = """
-----------------------------------------------------------
     Xray Docker Deployment Configurator (No Caddy)
-----------------------------------------------------------
This script will help you configure your Xray deployment
with support for Direct (for Iran users), Bridge, or Relay modes.
SSL certificate setup is also available.
-----------------------------------------------------------
    """
    print(banner)

def get_input(prompt_text, default=None):
    if default:
        prompt_text = f"{prompt_text} [Default: {default}]: "
    else:
        prompt_text = f"{prompt_text}: "
    user_input = input(prompt_text).strip()
    return user_input if user_input else default

def yes_no_input(prompt_text, default="y"):
    while True:
        response = get_input(prompt_text, default).lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Invalid input. Please enter 'y' or 'n'.")

def load_file(file_path):
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        sys.exit(1)

def save_file(content, file_path):
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"File saved: {file_path}")
    except Exception as e:
        print(f"Error saving {file_path}: {e}")
        sys.exit(1)

def update_config(config, upstream_uuid, bridge_uuid, outbound_domain, deployment_mode):
    config = re.sub(r'<UPSTREAM-UUID>', upstream_uuid, config)
    config = re.sub(r'<BRIDGE-UUID>', bridge_uuid, config)
    config = re.sub(r'<DEPLOYMENT-MODE>', deployment_mode, config)
    if deployment_mode == "direct":
        config = re.sub(r'<OUTBOUND-DOMAIN>', "", config)
    else:
        config = re.sub(r'<OUTBOUND-DOMAIN>', outbound_domain, config)
    return config

def prompt_uuid(label):
    while True:
        user_uuid = get_input(f"Enter a UUID for {label} (leave empty to generate one)")
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
            print(f"Invalid UUID for {label}. Please try again or leave it empty to auto-generate.")

def prompt_outbound_domain():
    return get_input("Enter the outbound domain (e.g., usnode1.example.com)")

def prompt_deployment_mode():
    print("\nDeployment Mode Options:")
    print("1. Direct connection (all connections pass directly, no outbound server needed)")
    print("2. Bridge")
    print("3. Relay")
    while True:
        choice = get_input("Select deployment mode by entering 1, 2, or 3")
        if choice == "1":
            return "direct"
        elif choice == "2":
            return "bridge"
        elif choice == "3":
            return "relay"
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def update_config_file(config_path):
    print("\nStep 1: Updating Xray configuration file")
    config = load_file(config_path)
    print(f"\nOriginal config content:\n{config}\n")
    
    deployment_mode = prompt_deployment_mode()
    
    if deployment_mode == "direct":
        print("\n[Direct Mode] Using a common UUID for both upstream and bridge. Outbound server will not be used.")
        common_uuid = prompt_uuid("common")
        upstream_uuid = common_uuid
        bridge_uuid = common_uuid
        outbound_domain = ""
    else:
        same_uuid = yes_no_input("Do you want to use the same UUID for both upstream and bridge?")
        if same_uuid:
            common_uuid = prompt_uuid("common")
            upstream_uuid = common_uuid
            bridge_uuid = common_uuid
        else:
            upstream_uuid = prompt_uuid("upstream")
            bridge_uuid = prompt_uuid("bridge")
        outbound_domain = prompt_outbound_domain()
    
    updated_config = update_config(config, upstream_uuid, bridge_uuid, outbound_domain, deployment_mode)
    print(f"\nUpdated configuration:\n{updated_config}\n")
    save_file(updated_config, config_path)
    print("Xray configuration updated successfully.\n")

def install_certbot():
    print("\nInstalling Certbot...")
    if os.path.exists('/etc/debian_version'):
        run_command("sudo apt-get update")
        run_command("sudo apt-get install -y certbot python3-certbot-nginx")
    elif os.path.exists('/etc/redhat-release'):
        run_command("sudo yum install -y epel-release")
        run_command("sudo yum install -y certbot python3-certbot-nginx")
    else:
        print("Error: Unsupported distribution")
        sys.exit(1)

def obtain_certificate_certbot(domain):
    print(f"\nObtaining SSL certificate for {domain} using Certbot...")
    run_command(f"sudo certbot --nginx -d {domain}")

def install_certificate_certbot(domain, install_folder):
    fullchain_src = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
    privkey_src = f"/etc/letsencrypt/live/{domain}/privkey.pem"
    fullchain_dest = os.path.join(install_folder, "xray.crt")
    privkey_dest = os.path.join(install_folder, "xray.key")
    print(f"Copying certificate files to {install_folder}...")
    run_command(f"sudo cp {fullchain_src} {fullchain_dest}")
    run_command(f"sudo cp {privkey_src} {privkey_dest}")

def install_acme_sh():
    print("\nInstalling acme.sh...")
    run_command("curl https://get.acme.sh | sh")

def register_acme_sh_account():
    email = get_input("Enter your email address for acme.sh account registration")
    print("\nChoose ACME server for registration:")
    print("1. Let's Encrypt (recommended)")
    print("2. ZeroSSL")
    while True:
        choice = get_input("Select server (1 or 2)", "1")
        if choice == "1":
            server = "letsencrypt"
            break
        elif choice == "2":
            server = "zerossl"
            break
        else:
            print("Invalid choice. Please enter 1 or 2.")
    if server == "zerossl":
        eab_kid = get_input("Enter your ZeroSSL EAB kid")
        eab_hmac = get_input("Enter your ZeroSSL EAB hmac key")
        command = f"~/.acme.sh/acme.sh --register-account -m {email} --server zerossl --eab-kid {eab_kid} --eab-hmac {eab_hmac}"
    else:
        command = f"~/.acme.sh/acme.sh --register-account -m {email} --server letsencrypt"
    run_command(command)

def obtain_certificate_acme_sh(domain):
    print(f"\nObtaining SSL certificate for {domain} using acme.sh...")
    run_command(f"sudo ~/.acme.sh/acme.sh --issue -d {domain} --standalone --debug -k ec-256")

def install_certificate_acme_sh(domain, install_folder):
    fullchain_path = os.path.join(install_folder, "xray.crt")
    key_path = os.path.join(install_folder, "xray.key")
    run_command(f"sudo ~/.acme.sh/acme.sh --installcert -d {domain} --fullchainpath {fullchain_path} --keypath {key_path}")

def update_docker_compose_file():
    print("\nStep 2: Updating Docker Compose configuration to skip Caddy")
    docker_compose_file = './docker-compose.yml'
    content = load_file(docker_compose_file)
    # Remove Caddy service configuration block if it exists.
    content = re.sub(
        r'caddy:.*depends_on:.*- xray.*ports:.*- "80:80".*- "443:443".*volumes:.*- \./caddy/Caddyfile:/etc/caddy/Caddyfile.*- \./caddy/web/:/usr/share/caddy.*- \./caddy/data/:/data/caddy/.*- \./caddy/config/:/config/caddy',
        '', content, flags=re.DOTALL
    )
    save_file(content, docker_compose_file)
    print("Docker Compose file updated successfully (Caddy configuration removed).\n")

def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        sys.exit(1)

def main():
    print_banner()
    
    config_path = get_input("Enter the path to config.json", "./xray/config/config.json")
    update_config_file(config_path)
    
    update_docker_compose_file()
    
    if yes_no_input("Do you want to install SSL certificates?", "y"):
        install_folder = os.path.dirname(os.path.abspath(config_path))
        domain_for_cert = get_input("Enter the domain for SSL certificate (e.g., example.com)")
        cert_tool = get_input("Choose the certificate tool (certbot/acme.sh)", "certbot").lower()

        if cert_tool == 'certbot':
            install_certbot()
            obtain_certificate_certbot(domain_for_cert)
            install_certificate_certbot(domain_for_cert, install_folder)
        elif cert_tool == 'acme.sh':
            install_acme_sh()
            register_acme_sh_account()
            obtain_certificate_acme_sh(domain_for_cert)
            install_certificate_acme_sh(domain_for_cert, install_folder)
        else:
            print("Error: Invalid certificate tool choice")
            sys.exit(1)
        print("Certificates have been installed and configured successfully.\n")
    else:
        print("Certificate installation skipped.\n")
    
    print("Deployment configuration completed successfully.")

if __name__ == "__main__":
    main()
