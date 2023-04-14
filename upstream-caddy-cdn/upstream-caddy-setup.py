#!/usr/bin/python3

import base64
import json
import uuid
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

    print('Upstream UUID:')
    print(upstreamUUID)
    print('\nDone!')

# Function to create a key


def create_key():
    path = Path(__file__).parent

    config_file = open(
        str(path.joinpath('xray/config/config.json')), 'r', encoding='utf-8')
    config = json.load(config_file)

    caddy = open(str(path.joinpath('caddy/Caddyfile')),
                 'r', encoding='utf-8').read()

    uuid = config['inbounds'][0]['settings']['clients'][0]['id']
    domain = caddy[:caddy.find(' {')]

    j = json.dumps({
        "v": "2", "ps": domain, "add": domain, "port": "443", "id": uuid, "aid": "0", "net": "ws", "type": "none",
        "host": domain, "path": "/ws", "tls": "tls"
    })

    vless_url = "vmess://" + \
        base64.b64encode(j.encode('ascii')).decode('ascii')
    print("VLESS URL:", vless_url)

    # Export the generated key in the Caddy webroot as a file
    key_file_path = path.joinpath('caddy/web/key.txt')
    with open(str(key_file_path), 'w', encoding='utf-8') as key_file:
        key_file.write(vless_url)

    # Provide a subscription link for users
    subscription_url = f"http://{domain}/key.txt"
    print("Subscription URL:", subscription_url)

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
