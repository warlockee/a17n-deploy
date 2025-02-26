FROM python:3.10-alpine

# Install autossh, SSH client, and socat
RUN apk add --no-cache autossh openssh-client socat

# Install PyYAML so we can parse our YAML config
RUN pip install pyyaml

# Set up SSH directory structure
RUN mkdir -p /root/.ssh && \
    chmod 700 /root/.ssh

# Copy our entrypoint script and default config
COPY entrypoint.py /entrypoint.py
COPY config.yaml /config.yaml

# Copy SSH private key into the container
COPY id_rsa /root/.ssh/id_rsa
RUN chmod 600 /root/.ssh/id_rsa

# Use the Python script as the container entrypoint.
ENTRYPOINT ["python", "/entrypoint.py"]