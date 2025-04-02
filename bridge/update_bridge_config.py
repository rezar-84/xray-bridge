#!/usr/bin/python3

import os
import re
import sys
import uuid
import subprocess

def print_banner():
    banner = """
-----------------------------------------------------------
      Xray Docker Deployment Configurator (No Caddy)
-----------------------------------------------------------
This utility will configure your Xray deployment in one of the
following modes: Direct (for users in Iran), Bridge, or Relay.
It will also handle SSL certificate issuance and installation.
-----------------------------------------------------------
    """
    print(banner)

def get_input(prompt_text, default=None):
    if default:
        prompt = f"{prompt_text} [Default: {default}]: "
    else:
        prompt = f"{prompt_text}: "
    response = input(prompt).strip()
    return response if response else default

def yes_no_input(prompt_text, default="y"):
    while True:
        response = get_input(prompt_text, default).lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' or 'n'.")

def load_file(file_path):
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)

def save_file(content, file_path):
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f">> Updated file saved: {file_path}")
    except Exception as e:
        print(f"Error saving '{file_path}': {e}")
        sys.exit(1)

def update_config(content, upstream_uuid, bridge_uuid, outbound_domain, deployment_mode):
    # Replace placeholders with user-supplied values
    content = re.sub(r'<UPSTREAM-UUID>', upstream_uuid, content)
    content = re.sub(r'<BRIDGE-UUID>', bridge_uuid, content)
    content = re.sub(r'<DEPLOYMENT-MODE>', deployment_mode, content)
    if deployment_mode == "direct":
        content = re.sub(r'<OUTBOUND-DOMAIN>', "", content)
    else:
        content = re.sub(r'<OUTBOUND-DOMAIN>', outbound_domain, content)
    return content

def prompt_uuid(label):
    while True:
        user_uuid = get_input(f"Enter a UUID for {label} (leave empty to auto-generate)")
        if not user_uuid:
            generated = str(uuid.uuid4())
            with open(f"{label}_generated_uuid.txt", "w") as f:
                f.write(generated)
            print(f">> Generated UUID for {label}: {generated}")
            return generated
        try:
            uuid.UUID(user_uuid)
            return user_uuid
        except ValueError:
            print("Invalid UUID format. Please try again.")

def prompt_outbound_domain():
    return get_input("Enter the outbound domain (e.g., usnode1.example.com)")

def prompt_deployment_mode():
    print("\nDeployment Mode Options:")
    print("  1. Direct connection (all connections pass directly; no outbound server)")
    print("  2. Bridge")
    print("  3. Relay")
    while True:
        choice = get_input("Select deployment mode (enter 1, 2, or 3)")
        if choice == "1":
            return "direct"
        elif choice == "2":
            return "bridge"
        elif choice == "3":
            return "relay"
        else:
            print("Invalid selection. Please enter 1, 2, or 3.")

def update_config_file(config_path):
    print("\n[Step 1] Updating Xray configuration file...")
    content = load_file(config_path)
    
    deployment_mode = prompt_deployment_mode()
    if deployment_mode == "direct":
        print(">> Direct mode selected: A common UUID will be used; no outbound server required.")
        common_uuid = prompt_uuid("common")
        upstream_uuid = common_uuid
        bridge_uuid = common_uuid
        outbound_domain = ""
    else:
        if yes_no_input("Use the same UUID for both upstream and bridge?"):
            common_uuid = prompt_uuid("common")
            upstream_uuid = common_uuid
            bridge_uuid = common_uuid
        else:
            upstream_uuid = prompt_uuid("upstream")
            bridge_uuid = prompt_uuid("bridge")
        outbound_domain = prompt_outbound_domain()
    
    updated_content = update_config(content, upstream_uuid, bridge_uuid, outbound_domain, deployment_mode)
    save_file(updated_content, config_path)
    print(">> Xray configuration updated successfully.\n")

def update_docker_compose_file():
    print("[Step 2] Updating Docker Compose configuration (removing Caddy)...")
    dc_file = './docker-compose.yml'
    content = load_file(dc_file)
    # Remove any Caddy service configuration block.
    content = re.sub(
        r'caddy:.*depends_on:.*- xray.*ports:.*- "80:80".*- "443:443".*volumes:.*',
        '',
        content,
        flags=re.DOTALL
    )
    save_file(content, dc_file)
    print(">> Docker Compose file updated successfully.\n")

def install_certbot():
    print("[SSL] Installing Certbot...")
    if os.path.exists('/etc/debian_version'):
        run_command("sudo apt-get update && sudo apt-get install -y certbot python3-certbot-nginx")
    elif os.path.exists('/etc/redhat-release'):
        run_command("sudo yum install -y epel-release && sudo yum install -y certbot python3-certbot-nginx")
    else:
        print("Unsupported Linux distribution.")
        sys.exit(1)

def obtain_certificate_certbot(domain):
    print(f"[SSL] Issuing certificate for '{domain}' using Certbot...")
    run_command(f"sudo certbot --nginx -d {domain}")

def install_certificate_certbot(domain, install_folder):
    fullchain_src = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
    privkey_src = f"/etc/letsencrypt/live/{domain}/privkey.pem"
    fullchain_dest = os.path.join(install_folder, "xray.crt")
    privkey_dest = os.path.join(install_folder, "xray.key")
    print(">> Copying certificate files to installation folder...")
    run_command(f"sudo cp {fullchain_src} {fullchain_dest}")
    run_command(f"sudo cp {privkey_src} {privkey_dest}")

def install_acme_sh():
    acme_path = os.path.expanduser("~/.acme.sh/acme.sh")
    if os.path.exists(acme_path):
        print(">> acme.sh is already installed.")
    else:
        print("[SSL] Installing acme.sh...")
        run_command("curl https://get.acme.sh | sh")

def register_acme_sh_account():
    email = get_input("Enter your email address for acme.sh registration")
    print(">> Registering acme.sh account with Let's Encrypt (default)...")
    cmd = f"~/.acme.sh/acme.sh --register-account -m {email} --server letsencrypt"
    run_command(cmd)

def obtain_certificate_acme_sh(domain):
    print(f"[SSL] Issuing certificate for '{domain}' using acme.sh...")
    # Check if Cloudflare DNS API script exists.
    cf_dns_api = os.path.expanduser("~/.acme.sh/dnsapi/dns_cf.sh")
    use_cf = False
    if os.path.exists(cf_dns_api):
        use_cf = yes_no_input("Cloudflare DNS API detected. Use Cloudflare DNS for certificate issuance?", "n")
    if use_cf:
        cf_key = get_input("Enter your Cloudflare API Key")
        cf_email = get_input("Enter your Cloudflare Email")
        cmd = f"CF_Key={cf_key} CF_Email={cf_email} ~/.acme.sh/acme.sh --issue --dns dns_cf -d {domain} --debug -k ec-256"
    else:
        # Use standalone mode (no DNS challenge)
        cmd = f"sudo ~/.acme.sh/acme.sh --issue -d {domain} --standalone --debug -k ec-256"
    run_command(cmd)

def install_certificate_acme_sh(domain, install_folder):
    fullchain_path = os.path.join(install_folder, "xray.crt")
    key_path = os.path.join(install_folder, "xray.key")
    cmd = f"sudo ~/.acme.sh/acme.sh --installcert -d {domain} --fullchainpath {fullchain_path} --keypath {key_path}"
    run_command(cmd)

def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        sys.exit(1)

def main():
    print_banner()
    
    # Step 1: Update configuration
    config_path = get_input("Enter the path to your Xray config.json", "./xray/config/config.json")
    update_config_file(config_path)
    
    # Step 2: Update docker-compose file (remove Caddy service)
    update_docker_compose_file()
    
    # Step 3: SSL certificate issuance (optional)
    if yes_no_input("Do you want to install SSL certificates?", "y"):
        install_folder = os.path.dirname(os.path.abspath(config_path))
        domain_for_cert = get_input("Enter the domain for SSL certificate (e.g., example.com)")
        cert_tool = get_input("Choose the certificate tool (certbot/acme.sh)", "certbot").lower()
        
        if cert_tool == "certbot":
            install_certbot()
            obtain_certificate_certbot(domain_for_cert)
            install_certificate_certbot(domain_for_cert, install_folder)
        elif cert_tool == "acme.sh":
            install_acme_sh()
            register_acme_sh_account()
            obtain_certificate_acme_sh(domain_for_cert)
            install_certificate_acme_sh(domain_for_cert, install_folder)
        else:
            print("Invalid certificate tool choice.")
            sys.exit(1)
        print(">> Certificates have been issued and installed successfully.\n")
    else:
        print(">> SSL certificate installation skipped.\n")
    
    print("Deployment configuration completed successfully.")

if __name__ == "__main__":
    main()
