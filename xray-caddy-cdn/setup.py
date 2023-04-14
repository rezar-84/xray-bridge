#!/usr/bin/python3

import uuid
import json
from pathlib import Path

# LOAD CONFIG FILE

path = Path(__file__).parent.joinpath('xray/config.json')
file = open(str(path), 'r', encoding='utf-8')
config = json.load(file)

# INPUT: UPSTREAM UUID

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

# SAVE CONFIG FILE

content = json.dumps(config, indent=2)
open(str(path), 'w', encoding='utf-8').write(content)

# UPDATE CADDYFILE DOMAIN

caddy_path = Path(__file__).parent.joinpath('caddy/Caddyfile')
caddy_content = open(str(caddy_path), 'r', encoding='utf-8').read()

old_domain = caddy_content[:caddy_content.find(' {')]
new_domain = input("Enter new domain: ")

caddy_content = caddy_content.replace(old_domain, new_domain)
open(str(caddy_path), 'w', encoding='utf-8').write(caddy_content)

# PRINT OUT RESULT

print('Upstream UUID:')
print(upstreamUUID)
print('\nDone!')
