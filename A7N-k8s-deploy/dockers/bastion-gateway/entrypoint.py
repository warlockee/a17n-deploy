#!/usr/bin/env python3
import yaml
import subprocess
import time
import socket
import os
import sys
import signal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('bastion-gateway')

# Global variables
processes = {}
port_mappings = {}


def find_free_port():
    """Find a free port on the local system."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def spawn_processes(config):
    """Spawn processes for all mappings in the config."""
    global processes, port_mappings

    for mapping in config['mappings']:
        name = mapping['name']
        src = mapping['src']
        dst = mapping['dst']

        # Detect if the source is HTTPS from the URL
        is_https = src.lower().startswith('https://')

        logger.info(
            f"Processing mapping: {name}, src: {src}, dst: {dst}, HTTPS: {is_https}")

        try:
            # Parse source
            if is_https:
                # For HTTPS URLs, remove the protocol prefix
                src = src[8:]  # Remove 'https://'
            elif src.lower().startswith('http://'):
                # For HTTP URLs, remove the protocol prefix
                src = src[7:]  # Remove 'http://'

            src_host, src_port = src.split(':')
            src_port = int(src_port)

            # Parse destination
            dst_host, dst_port = dst.split(':')
            dst_port = int(dst_port)

            # Find a free local port
            local_port = find_free_port()
            port_mappings[name] = local_port
            # Store HTTPS status for restart
            port_mappings[f"{name}_is_https"] = is_https

            logger.info(f"For mapping {name}: Using local port {local_port}")

            # Start socat process based on protocol
            if is_https:
                socat_cmd = [
                    'socat',
                    f'TCP-LISTEN:{local_port},fork,rcvbuf=1024000,sndbuf=1024000',
                    f'OPENSSL:{src_host}:{src_port},verify=0,rcvbuf=1024000,sndbuf=1024000'
                ]
                logger.info(
                    f"Starting socat process with OPENSSL for {name}: {' '.join(socat_cmd)}")
            else:
                socat_cmd = [
                    'socat',
                    f'TCP-LISTEN:{local_port},fork,rcvbuf=1024000,sndbuf=1024000',
                    f'TCP:{src_host}:{src_port},rcvbuf=1024000,sndbuf=1024000'
                ]
                logger.info(
                    f"Starting socat process for {name}: {' '.join(socat_cmd)}")

            socat_process = subprocess.Popen(socat_cmd)
            processes[f"{name}_socat"] = socat_process

            logger.info(f"Starting tunnel for {name} to {dst_host}:{dst_port}")

            # Start autossh process
            autossh_cmd = [
                'autossh',
                '-M', '0',
                '-N',
                '-o', 'ServerAliveInterval=60',
                '-o', 'ServerAliveCountMax=3',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'TCPKeepAlive=yes',
                '-o', 'Compression=yes',
                '-v',
                '-i', '/root/.ssh/id_rsa',
                '-R', f'{dst_port}:localhost:{local_port}',
                f'root@{dst_host}'
            ]

            logger.info(
                f"Starting autossh process for {name}: {' '.join(autossh_cmd)}")
            autossh_process = subprocess.Popen(autossh_cmd)
            processes[f"{name}_autossh"] = autossh_process

        except Exception as e:
            logger.error(f"Error setting up mapping {name}: {str(e)}")


def check_processes(config):
    """Check processes and restart if needed."""
    global processes

    while True:
        for process_name, process in list(processes.items()):
            # Check if process is still running
            if process.poll() is not None:
                mapping_name = process_name.split('_')[0]
                process_type = process_name.split('_')[1]

                logger.warning(
                    f"Process {process_name} terminated with code {process.returncode}. Restarting...")

                # Find mapping in config
                mapping = next(
                    (m for m in config['mappings'] if m['name'] == mapping_name), None)

                if mapping:
                    try:
                        if process_type == 'socat':
                            local_port = port_mappings[mapping_name]

                            # Get the stored HTTPS status
                            is_https = port_mappings.get(
                                f"{mapping_name}_is_https", False)

                            # Get source information
                            src = mapping['src']

                            # Handle protocol prefix if present
                            if is_https:
                                if src.lower().startswith('https://'):
                                    src = src[8:]  # Remove 'https://'
                            elif src.lower().startswith('http://'):
                                src = src[7:]  # Remove 'http://'

                            src_host, src_port = src.split(':')
                            src_port = int(src_port)

                            # Start the appropriate socat command based on the protocol
                            if is_https:
                                socat_cmd = [
                                    'socat',
                                    f'TCP-LISTEN:{local_port},fork,rcvbuf=1024000,sndbuf=1024000',
                                    f'OPENSSL:{src_host}:{src_port},verify=0,rcvbuf=1024000,sndbuf=1024000'
                                ]
                                logger.info(
                                    f"Restarting socat process with OPENSSL for {mapping_name}: {' '.join(socat_cmd)}")
                            else:
                                socat_cmd = [
                                    'socat',
                                    f'TCP-LISTEN:{local_port},fork,rcvbuf=1024000,sndbuf=1024000',
                                    f'TCP:{src_host}:{src_port},rcvbuf=1024000,sndbuf=1024000'
                                ]
                                logger.info(
                                    f"Restarting socat process for {mapping_name}: {' '.join(socat_cmd)}")

                            socat_process = subprocess.Popen(socat_cmd)
                            processes[f"{mapping_name}_socat"] = socat_process

                        elif process_type == 'autossh':
                            local_port = port_mappings[mapping_name]
                            dst_host, dst_port = mapping['dst'].split(':')
                            dst_port = int(dst_port)

                            autossh_cmd = [
                                'autossh',
                                '-M', '0',
                                '-N',
                                '-o', 'ServerAliveInterval=60',
                                '-o', 'ServerAliveCountMax=3',
                                '-o', 'StrictHostKeyChecking=no',
                                '-o', 'TCPKeepAlive=yes',
                                '-o', 'Compression=yes',
                                '-v',
                                '-i', '/root/.ssh/id_rsa',
                                '-R', f'{dst_port}:localhost:{local_port}',
                                f'root@{dst_host}'
                            ]

                            logger.info(
                                f"Restarting autossh process for {mapping_name}: {' '.join(autossh_cmd)}")
                            autossh_process = subprocess.Popen(autossh_cmd)
                            processes[f"{mapping_name}_autossh"] = autossh_process
                    except Exception as e:
                        logger.error(
                            f"Error restarting process {process_name}: {str(e)}")

        time.sleep(10)


def signal_handler(sig, frame):
    """Handle signals to terminate the program cleanly."""
    logger.info("Received signal to terminate. Shutting down...")

    for process_name, process in processes.items():
        logger.info(f"Terminating process {process_name}")
        process.terminate()

    sys.exit(0)


def main():
    """Main function."""
    # Load configuration
    logger.info("Loading configuration from /config.yaml")
    try:
        with open('/config.yaml', 'r') as file:
            config = yaml.safe_load(file)
            logger.info(f"Loaded configuration: {config}")
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        return

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Spawn processes
    spawn_processes(config)

    # Check processes
    check_processes(config)


if __name__ == '__main__':
    main()

# Add exponential backoff for connection attempts
