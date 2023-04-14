#!/usr/bin/python3

import base64
import json
import uuid
import base64
from pathlib import Path

# Function to set up the server


def setup_server():
    path = Path(__file__).parent.joinpath('xray/config/config.json')
    file = open(str(path), 'r', encoding='utf-8')
    config = json.load(file)

    defaultUUID = config['inbounds'][0]['settings']['clients'][0]['id']
    if defaultUUID == '<UPSTREAM-UUID>':
        message = "Upstream UUID: (Leave empty to generate a random one)\n"
    else:
        message = f"Upstream UUID: (Leave empty to use `{defaultUUID}`)\n"

    upstreamUUID = input(message)
    if upstreamUUID == '':
        if defaultUUID == '<UPSTREAM-UUID>':
            upstreamUUID = str(uuid.uuid4())
        else:
            upstreamUUID = defaultUUID

    config['inbounds'][0]['settings']['clients'][0]['id'] = upstreamUUID

    content = json.dumps(config, indent=2)
    open(str(path), 'w', encoding='utf-8').write(content)

    # Update Caddyfile with domain
    domain = input("Enter your domain: ")

    caddyfile_path = Path(__file__).parent.joinpath('caddy/Caddyfile')
    caddyfile_content = f"{domain} {{\n"
    caddyfile_content += "  root * /usr/share/caddy\n\n"
    caddyfile_content += "  @websockets {\n"
    caddyfile_content += "    header Connection *Upgrade*\n"
    caddyfile_content += "    header Upgrade    websocket\n"
    caddyfile_content += "  }\n\n"
    caddyfile_content += "  reverse_proxy @websockets xray:1310/ws\n\n"
    caddyfile_content += "  route {\n"
    caddyfile_content += "    reverse_proxy /ws xray:1310\n"
    caddyfile_content += "    file_server\n"
    caddyfile_content += "  }\n\n"
    caddyfile_content += "  log {\n"
    caddyfile_content += "    output stdout\n"
    caddyfile_content += "  }\n"
    caddyfile_content += "}"

    with open(str(caddyfile_path), 'w', encoding='utf-8') as caddyfile:
        caddyfile.write(caddyfile_content)

    print('Upstream UUID:')
    print(upstreamUUID)
    print('\nDone!')

# Function to create a key


import base64

def create_key():
    path = Path(__file__).parent

    config_file = open(str(path.joinpath('xray/config/config.json')), 'r', encoding='utf-8')
    config = json.load(config_file)

    caddy = open(str(path.joinpath('caddy/Caddyfile')), 'r', encoding='utf-8').read()

    uuid = config['inbounds'][0]['settings']['clients'][0]['id']
    domain = caddy[:caddy.find(' {')]

    vless_url = f"vless://{uuid}@{domain}:443?type=ws&host={domain}&path=%2Fws&tls=tls&net=ws&encryption=none"

    base64_vless_url = base64.b64encode(vless_url.encode('ascii')).decode('ascii')

    key_file_dir = path.joinpath('caddy/web/')
    key_file_dir.mkdir(parents=True, exist_ok=True)

    key_file_name = f"{domain.split('.')[0]}_key.txt"
    key_file_path = path.joinpath(f'caddy/web/{key_file_name}')

    with open(str(key_file_path), 'w', encoding='utf-8') as key_file:
        key_file.write(base64_vless_url)

    subscription_url = f"http://{domain}/{key_file_name}"

    print("VLESS URL (base64 encoded):")
    print(base64_vless_url)
    print("\nSubscription URL:")
    print(subscription_url)


# Main function


def main():
    print("Choose an option:")
    print("1. Set up server")
    print("2. Create a key")
    choice = input("Enter the number of your choice: ")

    if choice == "1":
        setup_server()
    elif choice == "2":
        create_key()
    else:
        print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
