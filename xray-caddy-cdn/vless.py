#!/usr/bin/python3
import json
import re
import base64
import uuid


def read_xray_config():
    with open("xray/config/config.json", "r") as file:
        config = json.load(file)
    return config


def read_caddyfile():
    with open("caddy/Caddyfile", "r") as file:
        caddyfile_contents = file.read()
    return caddyfile_contents


def get_domain(caddyfile_contents):
    domain = re.search(
        r'^(http[s]?://)?([a-zA-Z0-9\-.]+)', caddyfile_contents, re.MULTILINE)
    if domain:
        return domain.group(2)
    else:
        raise ValueError("Domain not found in Caddyfile")


def get_port_and_encryption(xray_config):
    inbounds = xray_config.get("inbounds", [])
    for inbound in inbounds:
        protocol = inbound.get("protocol")
        if protocol == "vless":
            port = inbound.get("port")
            settings = inbound.get("settings", {})
            clients = settings.get("clients", [])
            if clients:
                client = clients[0]
                encryption = client.get("encryption", "none")
                return port, encryption
    raise ValueError("VLESS protocol not found in Xray config")


def create_vless_key(domain, port, uuid, encryption):
    vless_url = f"vless://{uuid}@{domain}:{port}?encryption={encryption}&type=tcp&security=tls"
    return vless_url


def base64_encode_vless_key(vless_key):
    return base64.urlsafe_b64encode(vless_key.encode()).decode('utf-8')


def main():
    xray_config = read_xray_config()
    caddyfile_contents = read_caddyfile()
    domain = get_domain(caddyfile_contents)
    port, encryption = get_port_and_encryption(xray_config)
    uuid_key = str(uuid.uuid4())

    vless_key = create_vless_key(domain, port, uuid_key, encryption)
    base64_vless_key = base64_encode_vless_key(vless_key)

    print("Domain:", domain)
    print("VLESS Key (Normal):", vless_key)
    print("VLESS Key (Base64 Encoded):", base64_vless_key)


if __name__ == "__main__":
    main()
