# Bastion Gateway

A Docker container that creates a secure tunnel between an internal service and an external host through a bastion server.

## Prerequisites

1. Docker installed on your system
2. SSH private key for authentication

## Setup

1. Place your SSH private key (`id_rsa`) in the same directory as the Dockerfile
2. Configure your mappings in `config.yaml`

## Building the Container

```bash
docker build -t bastion-gateway .
```

## Running the Container

Basic run command:
```bash
docker run -d \
  --name bastion-gateway \
  --network=host \
  --restart unless-stopped \
  bastion-gateway
```

## Configuration

Edit `config.yaml` to configure your mappings:

```yaml
mappings:
  - name: mapping1
    src: "internal-service:port"  # e.g., "10.21.100.70:11434"
    dst: "external-host:port"     # e.g., "ec2-instance:30001"
    remote_host: "external-host"  # e.g., "ec2-instance"
    identity_file: "id_rsa"      # Make sure this matches your private key filename
```

## Monitoring

View container logs:
```bash
docker logs bastion-gateway
```

Check container status:
```bash
docker ps -a | grep bastion-gateway
```

## Network Mode

This container uses `--network=host` because:
1. It needs to access internal services on the host network
2. The socat process needs to bind to ports on the host machine
3. The SSH tunnels need to operate on the host network level 