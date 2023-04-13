# Xray Deployment for DPI Bypass in Iran

This project aims to provide a Docker Compose setup to deploy Xray in order to bypass DPI internet censorship in Iran. The system consists of two nodes: a bridge server located in an Iranian datacenter and an upstream server located outside Iran. Clients connect to the bridge server, which routes the traffic to the free internet through the upstream server.

## Project Structure

- `bridge/`: Contains the Docker Compose and Xray configuration files for the bridge server.
  - `xray/`: Contains the Xray configuration files for the bridge server.
    - `config/`: Contains the `config.json` file for the bridge server.
- `upstream/`: Contains the Docker Compose and Xray configuration files for the upstream server.
  - `xray/`: Contains the Xray configuration files for the upstream server.
    - `config/`: Contains the `config.json` file for the upstream server.
- `update_bridge_config.py`: Python script to update the bridge server configuration.
- `update_upstream_config.py`: Python script to update the upstream server configuration.

## Prerequisites

- Docker
- Docker Compose
- Python 3

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
