import json
import base64


def load_config(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)


def generate_vless_url(bridge_config, upstream_config):
    bridge_inbound = bridge_config['inbounds'][0]
    upstream_inbound = upstream_config['inbounds'][0]

    bridge_client = bridge_inbound['settings']['clients'][0]
    upstream_client = upstream_inbound['settings']['clients'][0]

    vless_url = {
        "v": "2",
        "ps": "",
        "add": bridge_client['id'],
        "port": str(bridge_inbound['port']),
        "id": upstream_client['id'],
        "aid": str(upstream_client['level']),
        "net": upstream_inbound['streamSettings']['network'],
        "type": "none",
        "host": "",
        "path": upstream_inbound['streamSettings']['wsSettings']['path'],
        "tls": upstream_inbound['streamSettings']['security']
    }

    vless_url_str = json.dumps(vless_url, separators=(',', ':'))
    vless_url_b64 = base64.urlsafe_b64encode(
        vless_url_str.encode()).decode().strip('=')
    return f"vless://{vless_url_b64}"


bridge_config = load_config('bridge/config/config.json')
upstream_config = load_config('upstream/config/config.json')

vless_url = generate_vless_url(bridge_config, upstream_config)
print(vless_url)
