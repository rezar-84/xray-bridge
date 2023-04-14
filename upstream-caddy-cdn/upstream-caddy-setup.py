#!/usr/bin/python3

import base64
import json
import uuid
import base64
from pathlib import Path

# Function to set up the server


def setup_server():
    # Get user input for domain
    domain = input("Please enter your domain name: ")

    # LOAD CONFIG FILE
    path = Path(__file__).parent.joinpath('xray/config/config.json')
    file = open(str(path), 'r', encoding='utf-8')
    config = json.load(file)

    # INPUT: UPSTREAM UUID
    defaultUUID = config['inbounds'][0]['settings']['clients'][0]['id']
    if defaultUUID == '<UPPSTREAM-UUID>':
        message = "Upstream UUID: (Leave empty to generate a random one)\n"
    else:
        message = f"Upstream UUID: (Leave empty to use `{defaultUUID}`)\n"

    upstreamUUID = input(message)
    if upstreamUUID == '':
        if defaultUUID == '<UPSTREAM-UUID>':
            upstreamUUID = str(uuid.uuid4())
        else:
            upstreamUUID = defaultUUID

    # SET UPSTREAM UUID
    config['inbounds'][0]['settings']['clients'][0]['id'] = upstreamUUID
    config['inbounds'][1]['settings']['clients'][0]['id'] = upstreamUUID

    defaultEmail = config['inbounds'][0]['settings']['clients'][0]['email']
    if defaultEmail == '<USER-EMAIL>':
        userEmail = input("Enter your email: ")
    else:
        userEmail = defaultEmail

    config['inbounds'][0]['settings']['clients'][0]['email'] = userEmail

    # SET WEBSOCKET PATH
    websocket_path = f"/{upstreamUUID}"
    config['inbounds'][0]['settings']['fallbacks'][1]['path'] = websocket_path
    config['inbounds'][1]['streamSettings']['wsSettings']['path'] = websocket_path

    # SET CERTIFICATE AND KEY PATHS
    cert_path = f"/data/caddy/certificates/acme-v02.api.letsencrypt.org-directory/{domain}"
    config['inbounds'][0]['streamSettings']['tlsSettings'][
        'certificates'][0]['certificateFile'] = f"{cert_path}/{domain}.crt"
    config['inbounds'][0]['streamSettings']['tlsSettings'][
        'certificates'][0]['keyFile'] = f"{cert_path}/{domain}.key"

    # SAVE CONFIG FILE
    content = json.dumps(config, indent=2)
    open(str(path), 'w', encoding='utf-8').write(content)

    # Update Caddyfile with domain
    caddyfile_path = Path(__file__).parent.joinpath('caddy/Caddyfile')
    caddyfile_content = f"{domain} {{\n"
    caddyfile_content += "  root * /usr/share/caddy\n\n"
    caddyfile_content += "  @websockets {\n"
    caddyfile_content += "    header Connection *Upgrade*\n"
    caddyfile_content += "    header Upgrade    websocket\n"
    caddyfile_content += "  }\n\n"
    caddyfile_content += f"  reverse_proxy @websockets xray:1310{websocket_path}\n\n"
    caddyfile_content += "  route {\n"
    caddyfile_content += f"    reverse_proxy {websocket_path} xray:1310\n"
    caddyfile_content += "    file_server\n"
    caddyfile_content += "  }\n\n"
    caddyfile_content += "  log {\n"
    caddyfile_content += "output stdout\n"
    caddyfile_content += "  }\n"
    caddyfile_content += "}"


with open(str(caddyfile_path), 'w', encoding='utf-8') as caddyfile:
    caddyfile.write(caddyfile_content)

# Create client JSON configuration
client_config = {
    "log": {
        "loglevel": "warning"
    },
    "inbounds": [
        {
            "port": 10800,
            "listen": "127.0.0.1",
            "protocol": "socks",
            "settings": {
                "udp": True
            }
        }
    ],
    "outbounds": [
        {
            "protocol": "vless",
            "settings": {
                "vnext": [
                    {
                        "address": domain,
                        "port": 443,
                        "users": [
                            {
                                "id": upstreamUUID,
                                "encryption": "none",
                                "level": 0
                            }
                        ]
                    }
                ]
            },
            "streamSettings": {
                "network": "ws",
                "security": "tls",
                "tlsSettings": {
                    "serverName": domain
                },
                "wsSettings": {
                    "path": websocket_path
                }
            }
        }
    ]
}

# Save client configuration to a file
client_config_path = Path(__file__).parent.joinpath(
    f'client_configs/{domain}_client_config.json')
client_config_path.parent.mkdir(parents=True, exist_ok=True)
with open(str(client_config_path), 'w', encoding='utf-8') as client_config_file:
    json.dump(client_config, client_config_file, indent=2)

print('Upstream UUID:')
print(upstreamUUID)
print('\nClient configuration file:')
print(client_config_path)
print('\nDone!')


# Function to create a key


def create_key():
    path = Path(__file__).parent

    # Use the client_config.json file
    config_file = open(
        str(path.joinpath('client_config.json')), 'r', encoding='utf-8')
    config = json.load(config_file)

    uuid = config['outbounds'][0]['settings']['vnext'][0]['users'][0]['id']
    domain = config['outbounds'][0]['settings']['vnext'][0]['address']

    # WebSocket + TLS
    vless_ws_url = f"vless://{uuid}@{domain}:443?type=ws&host={domain}&path=%2Fws&tls=tls&net=ws&encryption=none"

    # TCP + XTLS (assuming XTLS is implemented)
    # vless_xtls_url = f"vless://{uuid}@{domain}:443?type=tcp&host={domain}&tls=xtls&net=tcp&encryption=none"

    base64_vless_ws_url = base64.b64encode(
        vless_ws_url.encode('ascii')).decode('ascii')
    # base64_vless_xtls_url = base64.b64encode(vless_xtls_url.encode('ascii')).decode('ascii')

    key_file_dir = path.joinpath('caddy/web/')
    key_file_dir.mkdir(parents=True, exist_ok=True)

    key_file_name = f"{domain.split('.')[0]}_key.txt"
    key_file_path = path.joinpath(f'caddy/web/{key_file_name}')

    with open(str(key_file_path), 'w', encoding='utf-8') as key_file:
        key_file.write(base64_vless_ws_url + '\n')
        # key_file.write(base64_vless_xtls_url + '\n')

    subscription_url = f"http://{domain}/{key_file_name}"

    print("WebSocket + TLS VLESS URL (base64 encoded):")
    print(base64_vless_ws_url)
    # print("\nTCP + XTLS VLESS URL (base64 encoded):")
    # print(base64_vless_xtls_url)
    print("\nSubscription URL:")
    print(subscription_url)

# Main function


def main():
    while True:
        print("Choose an option:")
        print("1. Setup server")
        print("2. Create a new key")
        print("3. Exit")
        choice = input("Enter the number of your choice: ")

        if choice == '1':
            setup_server()
        elif choice == '2':
            create_key()
        elif choice == '3':
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
