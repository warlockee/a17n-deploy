import os
import time
import subprocess
import yaml
import signal
import socket

CONFIG_FILE = "/config.yaml"
SSH_CONFIG_DIR = "/root/.ssh"
SSH_PRIVATE_KEY = "/root/.ssh/id_rsa"


def load_config():
    with open(CONFIG_FILE, "r") as f:
        return yaml.safe_load(f)


def find_available_port():
    """Find an available port on localhost by creating a socket and letting the OS assign a port."""
    sock = socket.socket()
    sock.bind(('', 0))  # Bind to any available port
    port = sock.getsockname()[1]
    sock.close()
    return port


def spawn_process_with_retry(cmd, max_retries=5, initial_delay=1):
    for attempt in range(max_retries):
        try:
            proc = subprocess.Popen(cmd)
            return proc
        except Exception as e:
            if attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)
                print(f"Connection attempt failed, retrying in {delay}s: {e}")
                time.sleep(delay)
            else:
                raise


def spawn_processes(mappings):
    processes = {}
    mapping_configs = {}  # Store mapping configs for restart purposes

    for mapping in mappings:
        name = mapping.get("name")
        if not name:
            print("Skipping mapping without a name:", mapping)
            continue

        # Get configuration for autossh
        src = mapping.get("src", "")
        dst = mapping.get("dst", "")

        if not dst:
            print(f"Skipping mapping '{name}': dst not specified")
            continue

        try:
            # Parse source and destination connection info
            src_host, src_port = src.split(":")
            dst_host, dst_port = dst.split(":")
        except Exception as e:
            print(f"Error parsing src/dst in mapping {mapping}: {e}")
            continue

        # Store mapping configuration for potential restarts
        mapping_configs[name] = {
            "src": src,
            "dst": dst,
            "src_host": src_host,
            "src_port": src_port,
            "dst_host": dst_host,
            "dst_port": dst_port
        }

        # Dynamically find an available port
        bastion_port = find_available_port()
        mapping_configs[name]["bastion_port"] = bastion_port
        print(f"Using local port {bastion_port} for mapping '{name}'")

        # Step 1: Set up socat to listen on the bastion (using dynamic port)
        # Listen on dynamically allocated port and forward to the internal service (src)
        # Optimize with larger buffers for better throughput
        socat_cmd = [
            "socat",
            f"TCP-LISTEN:{bastion_port},fork,rcvbuf=1024000,sndbuf=1024000",
            f"TCP:{src},rcvbuf=1024000,sndbuf=1024000"
        ]

        print(f"Starting socat for mapping '{name}':", " ".join(socat_cmd))
        socat_proc = spawn_process_with_retry(socat_cmd)
        processes[f"{name}_socat"] = socat_proc

        # Step 2: Set up autossh to forward from bastion to destination
        # Build the autossh command with optimized TCP settings
        autossh_cmd = [
            "autossh",
            "-M", "0",  # Disable autossh's monitoring
            "-N",       # Don't execute remote command
            "-o", "ServerAliveInterval=60",
            "-o", "ServerAliveCountMax=3",
            "-o", "StrictHostKeyChecking=no",
            "-o", "TCPKeepAlive=yes",
            "-o", "Compression=yes",  # Enable compression for better throughput
            "-v",       # Verbose mode
            "-i", SSH_PRIVATE_KEY  # Use the standard private key path
        ]

        # Create the remote tunnel
        autossh_cmd.extend([
            "-R", f"{dst_port}:localhost:{bastion_port}",
            f"root@{dst_host}"  # Use the hostname from dst
        ])

        print(f"Starting autossh for mapping '{name}':", " ".join(autossh_cmd))
        autossh_proc = spawn_process_with_retry(autossh_cmd)
        processes[f"{name}_autossh"] = autossh_proc

    return processes, mapping_configs


def kill_processes(processes):
    for name, proc in processes.items():
        print(f"Killing process '{name}' (pid {proc.pid})")
        proc.send_signal(signal.SIGTERM)
        proc.wait()
    processes.clear()


def check_tunnel_health(processes, mapping_configs):
    """Monitor and restart any failed processes."""
    for name, proc in list(processes.items()):
        if proc.poll() is not None:  # Process has terminated
            print(
                f"Process '{name}' died unexpectedly (exit code: {proc.returncode}). Restarting...")

            # Determine if this is a socat or autossh process and restart
            if name.endswith("_socat"):
                mapping_name = name[:-6]  # Remove "_socat" suffix
                if mapping_name in mapping_configs:
                    config = mapping_configs[mapping_name]
                    socat_cmd = [
                        "socat",
                        f"TCP-LISTEN:{config['bastion_port']},fork,rcvbuf=1024000,sndbuf=1024000",
                        f"TCP:{config['src']},rcvbuf=1024000,sndbuf=1024000"
                    ]
                    print(
                        f"Restarting socat for mapping '{mapping_name}':", " ".join(socat_cmd))
                    new_proc = spawn_process_with_retry(socat_cmd)
                    processes[name] = new_proc

            elif name.endswith("_autossh"):
                mapping_name = name[:-8]  # Remove "_autossh" suffix
                if mapping_name in mapping_configs:
                    config = mapping_configs[mapping_name]
                    autossh_cmd = [
                        "autossh",
                        "-M", "0",
                        "-N",
                        "-o", "ServerAliveInterval=60",
                        "-o", "ServerAliveCountMax=3",
                        "-o", "StrictHostKeyChecking=no",
                        "-o", "TCPKeepAlive=yes",
                        "-o", "Compression=yes",
                        "-v",
                        "-i", SSH_PRIVATE_KEY
                    ]
                    autossh_cmd.extend([
                        "-R", f"{config['dst_port']}:localhost:{config['bastion_port']}",
                        f"root@{config['dst_host']}"
                    ])
                    print(f"Restarting autossh for mapping '{mapping_name}':", " ".join(
                        autossh_cmd))
                    new_proc = spawn_process_with_retry(autossh_cmd)
                    processes[name] = new_proc


def main():
    last_mtime = 0
    processes = {}
    mapping_configs = {}

    while True:
        try:
            mtime = os.path.getmtime(CONFIG_FILE)
            if mtime != last_mtime:
                print("Config file changed; reloading mappings...")
                config = load_config()
                mappings = config.get("mappings", [])
                kill_processes(processes)
                processes, mapping_configs = spawn_processes(mappings)
                last_mtime = mtime

            # Check and restore any failed tunnel processes
            check_tunnel_health(processes, mapping_configs)

            time.sleep(5)
        except KeyboardInterrupt:
            print("Shutting down...")
            kill_processes(processes)
            break
        except Exception as e:
            print("Error:", e)
            time.sleep(5)


if __name__ == "__main__":
    main()

# Add exponential backoff for connection attempts
