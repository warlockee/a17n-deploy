FROM nvcr.io/nvidia/pytorch:23.07-py3

# Install additional dependencies
RUN DEBIAN_FRONTEND=noninteractive apt-get update -qq && \
    DEBIAN_FRONTEND=noninteractive apt-get install -qq -y \
    pciutils \
    lshw && \
    rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy the startup script
COPY vg_ollama_tifa.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/vg_ollama_tifa.sh

# Set environment variables
ENV OLLAMA_HOST=0.0.0.0
ENV OLLAMA_KEEP_ALIVE=1

# Expose Ollama port
EXPOSE 11434

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/vg_ollama_tifa.sh"] 