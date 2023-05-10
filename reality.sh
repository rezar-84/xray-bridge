#!/bin/bash

# Set default values
xray_container_name="xray-server"
xray_config_path="./xray-config"
xray_log_path="./xray-logs"

# Prompt for container name or use default
read -p "Enter a name for the Xray Docker container [default: xray-server]: " input
xray_container_name=${input:-$xray_container_name}

# Prompt for configuration path or use default
read -p "Enter a path for Xray configuration files [default: ./xray-config]: " input
xray_config_path=${input:-$xray_config_path}

# Prompt for log path or use default
read -p "Enter a path for Xray log files [default: ./xray-logs]: " input
xray_log_path=${input:-$xray_log_path}

# Generate Xray UUID or prompt for input
read -p "Enter a UUID for the Xray server or press enter to generate one automatically: " input
xray_uuid=${input:-$(cat /proc/sys/kernel/random/uuid)}

# Prompt for domain name or use default
read -p "Enter a domain name for the Xray server [default: example.com]: " input
domain=${input:-example.com}

# Create directories for Xray configuration and logs
mkdir -p $xray_config_path
mkdir -p $xray_log_path

# Create Xray configuration file
# Create Xray configuration file
cat << EOF > $xray_config_path/config.json
{
    "log": {
        "access": "/var/log/xray/access.log",
        "error": "/var/log/xray/error.log",
        "loglevel": "warning"
    },
    "inbounds": [
        {
            "port": 443,
            "protocol": "vless",
            "settings": {
                "clients": [
                    {
                        "id": "$xray_uuid",
                        "level": 0
                    }
                ],
                "decryption": "none",
                "fallbacks": [
                    {
                        "dest": 80
                    }
                ]
            },
            "streamSettings": {
                "network": "ws",
                "security": "xtls",
                "xtlsSettings": {
                    "minVersion": "1.3",
                    "alpn": [
                        "http/1.1"
                    ],
                    "certificates": [
                        {
                            "certificateFile": "/etc/xray/xray.crt",
                            "keyFile": "/etc/xray/xray.key",
                            "usage": [
                                "encipherment",
                                "signature"
                            ]
                        }
                    ],
                    "sessionTicket": true,
                    "sessionTicketKeyFile": "/etc/xray/session_ticket.key",
                    "fallbacks": [
                        {
                            "dest": 80
                        }
                    ]
                },
                "wsSettings": {
                    "path": "/"
                }
            }
        }
    ],
    "outbounds": [
        {
            "protocol": "freedom",
            "settings": {}
        },
        {
            "protocol": "blackhole",
            "tag": "blocked"
        }
    ],
    "routing": {
        "rules": [
            {
                "type": "field",
                "ip": [
                    "geoip:IR"
                ],
                "outboundTag": "blocked"
            },
            {
                "type": "field",
                "domain": [
                    "domain:.ir"
                ],
                "outboundTag": "blocked"
            },
            {
                "type": "field",
                "protocol": [
                    "bittorrent"
                ],
                "outboundTag": "blocked"
            }
        ]
    }
}
EOF


# Create self-signed Xray TLS certificate
openssl req -newkey rsa:2048 -nodes -keyout $xray_config_path/xray.key -x509 -days 365 -out $xray_config_path/xray.crt -subj "/C=US/ST=California/L=San Francisco/O=Example Corp/OU=IT Department/CN=$domain"

# Create session ticket encryption key
openssl rand -hex 48 > $xray_config_path/session_ticket.key

# Create docker-compose.yaml file
# Create docker-compose.yaml file
cat << EOF > docker-compose.yaml
version: '3.8'

services:
  xray-server:
    image: teddysun/xray
    container_name: $xray_container_name
    restart: always
    network_mode: host
    volumes:
      - ./xray-config:/etc/xray
      - ./xray-logs:/var/log/xray

volumes:
  xray-config:
    driver_opts:
      type: none
      device: "./xray-config"
      o: bind
  xray-logs:
    driver_opts:
      type: none
      device: "./xray-logs"
      o: bind
EOF

# Run Xray Docker container using Docker Compose
docker-compose up -d

echo "Xray server with XTLS Reality encryption mode and Iran IP blocking has been set up successfully."
