# Xray Deployment for DPI Bypass in Iran

This project aims to provide a Docker Compose setup to deploy Xray in order to bypass DPI internet censorship in Iran. The system consists of two nodes: a bridge server located in an Iranian datacenter and an upstream server located outside Iran. Clients connect to the bridge server, which routes the traffic to the free internet through the upstream server.

## Project Structure

- `bridge/`: Contains the Docker Compose and Xray configuration files for the bridge server.
  - `xray/`: Contains the Xray configuration files for the bridge server.
    - `config/`: Contains the `config.json` file for the bridge server.
    - `log/`: Contains the log file for the bridge server.
  - `caddy/`:Contains the `Caddyfile` for Caddyconfiguration. -`web`: Contains `index.html` and
  - `update_bridge_config.py`: Python script to update the bridge server configuration.
- `upstream/`: Contains the Docker Compose and Xray configuration files for the upstream server.
  - `xray/`: Contains the Xray configuration files for the upstream server.
    - `config/`: Contains the `config.json` file for the upstream server.
    - `log/`: Contains the `log.json` file for the upstream server.
  - `update_upstream_config.py`: Python script to update the upstream server configuration.
- `keymaker.py`:Python script to create vless keys to access service and output subscription
- `utils`: contains some tools

## Variables

- `bridge/xray/config/config.json` variables will be updated by `bridge/update_bridge_config.py`.
- `<UPSTREAM-UUID>` :Upstream UUID genrated by user.
- `<OUTBOUND-DOMAIN>`:Upstream domain address entered by user
- `<BRIDGE-UUID>` : Bridge UUID -`upstream/xray/config/config.json` variables will be updated by `upstream/docker-compose.yml`
- `<UPSTREAM-UUID>` :Upstream UUID.

## Prerequisites

- Docker
- Docker Compose
- Python 3

### Ubuntu

#### Installing Dependencies and Packages on Ubuntu

1. Update the package list and upgrade the system:

   ```bash
   sudo apt-get update
   sudo apt-get upgrade
   ```

2. Install Docker:

```bash
sudo apt-get install apt-transport-https ca-certificates curl software-properties-common lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io

```

3. Install Docker Compose:

```bash
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

4.Install Python 3 and pip:

```bash
sudo apt-get install python3 python3-pip
```

5.Verify the installations:

```bash
docker --version
docker-compose --version
python3 --version
pip3 --version
```

## Installation

1. Clone the repository:

```bash
git clone https://github.com/reza-84/xray-bridge.git
cd xray-bridge
```

2. Update the configuration files using the provided Python scripts:

- Update the bridge server configuration:

  ```bash
  python update_bridge_config.py
  ```

- Update the upstream server configuration:

  ```bash
  python update_upstream_config.py
  ```

3. Deploy the bridge server:

```bash
cd bridge
docker-compose up -d
```

4. Deploy the upstream server:

```bash
cd upstream
docker-compose up -d

```

## Usage

1. Connect your client to the bridge server using the provided VLESS configuration URL.

2. Enjoy unrestricted access to the internet.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
