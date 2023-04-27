import json
import uuid
import sys
import re
import subprocess
import os
import shutil


def load_file(file_path):
    with open(file_path, 'r') as f:
        return f.read()


def save_file(content, file_path):
    with open(file_path, 'w') as f:
        f.write(content)


def update_upstream_config(config_str, new_uuid):
    return re.sub(r'<UPSTREAM-UUID>', new_uuid, config_str)


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


def get_current_uuid(config_str):
    match = re.search(r'"id":\s*"([^"]+)"', config_str)
    if match:
        return match.group(1)
    return None


def update_upstream_config_file(config_path):
    config_str = load_file(config_path)
    current_uuid = get_current_uuid(config_str)
    if current_uuid:
        print(f"Current UUID in config file: {current_uuid}")
        use_current_uuid = input(
            "Do you want to use the current UUID? (yes/no): ").strip().lower()
        if use_current_uuid == 'yes':
            print("Using the current UUID.")
            return
    new_uuid = prompt_uuid()
    updated_config_str = update_upstream_config(config_str, new_uuid)
    save_file(updated_config_str, config_path)
    print("Upstream configuration updated successfully.")


def run_command(command):
    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        output = process.stdout.readline().decode('utf-8')
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
    rc = process.poll()
    if rc != 0:
        print(f"Error: {process.stderr.read().decode('utf-8')}")
        sys.exit(1)
    return process.stdout.read().decode('utf-8')


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
    run_command("source ~/.bashrc")


def register_acme_sh_account():
    email = input(
        "Enter your email address to register with acme.sh: ").strip()
    run_command(f"./acme.sh --register-account -m {email}")


def obtain_certificate_acme_sh(domain):
    print(f"Obtaining SSL certificate for domain {domain} using acme.sh...")
    run_command(
        f"sudo ~/.acme.sh/acme.sh --issue -d {domain} --standalone --debug -k ec-256")


def install_certificate_acme_sh(domain, config_path):
    fullchain_path = os.path.join(config_path, "xray.cer")
    key_path = os.path.join(config_path, "xray.key")
    run_command(
        f"sudo ~/.acme.sh/acme.sh --installcert -d {domain} --fullchainpath {fullchain_path} --keypath {key_path}")


def setup_auto_renewal_certbot():
    print("Setting up auto-renewal for SSL certificates using Certbot...")
    cron_job = "0 0,12 * * * python3 -c 'import random; import time; time.sleep(random.random() * 3600)' && certbot renew"
    run_command(
        f"(crontab -l 2>/dev/null; echo '{cron_job}') | sudo crontab -")


def update_certificate_paths(config_path, domain):
    with open(config_path, 'r') as f:
        config = json.load(f)

    cert_path = "/etc/letsencrypt/live/{}/fullchain.pem".format(domain)
    key_path = "/etc/letsencrypt/live/{}/privkey.pem".format(domain)

    config['inbounds'][0]['streamSettings']['tlsSettings']['certificates'][0]['certificateFile'] = cert_path
    config['inbounds'][0]['streamSettings']['tlsSettings']['certificates'][0]['keyFile'] = key_path

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


def main():
    config_path = input(
        "Enter the path to the upstream config.json or leave it empty to use the default (./xray/config/config.json): ").strip()
    if not config_path:
        config_path = "./xray/config/config.json"
    update_upstream_config_file(config_path)

    install_certs = input(
        "Do you want to install SSL certificates? (yes/no): ").strip().lower()
    if install_certs == 'yes':
        domain = input("Enter your domain name: ").strip()
        if not domain:
            print("Error: Invalid domain name")
            sys.exit(1)

        cert_tool = input(
            "Choose the certificate tool to use (certbot/acme.sh): ").strip().lower()
        if cert_tool == 'certbot':
            install_certbot()
            obtain_certificate_certbot(domain)
            setup_auto_renewal_certbot()
            update_certificate_paths(config_path, domain)
        elif cert_tool == 'acme.sh':
            install_acme_sh()
            register_acme_sh_account()
            obtain_certificate_acme_sh(domain)
            install_certificate_acme_sh(domain, config_path)
        else:
            print("Error: Invalid certificate tool choice")
            sys.exit(1)

        print("Certificates have been installed and configured successfully.")
    else:
        print("Certificates installation skipped.")


if __name__ == "__main__":
    main()
