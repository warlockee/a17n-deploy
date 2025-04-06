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

## Running as a Systemd Service

To run the bastion gateway as a systemd service for automatic startup and restarts, follow these steps:

1.  **Create the service file:**
    Create a file named `/etc/systemd/system/bastion-gateway.service` with the following content:

    ```ini
    [Unit]
    Description=Bastion Gateway Docker Container
    Requires=docker.service
    After=docker.service network-online.target

    [Service]
    Type=oneshot
    RemainAfterExit=yes
    WorkingDirectory=/etc/systemd/system/
    ExecStart=/bin/bash /etc/systemd/system/run-bastion.sh
    ExecStop=/usr/bin/docker stop bastion-gw
    ExecStop=/usr/bin/docker rm bastion-gw

    [Install]
    WantedBy=multi-user.target
    ```

2.  **Create the run script:**
    Create a helper script named `/etc/systemd/system/run-bastion.sh` with execute permissions (`chmod +x run-bastion.sh`). This script ensures the container is stopped and removed before starting a new one.

    ```bash
    #!/bin/bash
    docker stop bastion-gw || true && docker rm bastion-gw || true && docker run --pull always --name bastion-gw -d warlockee/bastion-gw:latest
    ```
    *Note:* Ensure the Docker image `warlockee/bastion-gw:latest` exists or replace it with your image name. Adjust the `docker run` command if you need different parameters (like network mode or volume mounts based on the basic run command above). For instance, if you built the image locally as `bastion-gateway` and need host networking, the command would look more like:
    `docker run --network=host --restart unless-stopped --name bastion-gw -d bastion-gateway`

3.  **Enable and start the service:**

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable bastion-gateway.service
    sudo systemctl start bastion-gateway.service
    ```

4.  **Check the service status:**

    ```bash
    sudo systemctl status bastion-gateway.service
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