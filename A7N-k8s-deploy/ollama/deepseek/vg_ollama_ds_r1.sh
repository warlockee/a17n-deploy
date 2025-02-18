#!/bin/bash
set -euo pipefail

exec > >(tee /var/log/startup.log) 2>&1
set -x

# install deps
DEBIAN_FRONTEND=noninteractive apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -qq -y curl pciutils lshw

# install Ollama
curl -fsSL https://ollama.com/install.sh | sh

export OLLAMA_HOST=0.0.0.0
export OLLAMA_KEEP_ALIVE=-1
ollama serve &

# wait ollame serve
until ollama list >/dev/null 2>&1; do
    echo "等待 Ollama 服务启动..."
    sleep 5
done

# The absolute path of the model directory that download buy huggingface
# sudo apt-get install git-lfs
# git clone https://huggingface.co/deepseek-ai/DeepSeek-R1
# This path is the virginia cluster path
MODEL_DIR="/mnt/share/ckpt/DeepSeek-R1"
if [ -d "$MODEL_DIR" ]; then
    cd "$MODEL_DIR" || exit 1
    ollama create DeepSeek-R1 -f Modelfile
    
    # wait model setup
    until ollama list | grep -q "DeepSeek-R1"; do
        echo "等待模型加载..."
        sleep 10
    done
else
    echo "错误：模型目录不存在于 $MODEL_DIR" >&2
    exit 1
fi

while true; do
    if ! pgrep -x "ollama" >/dev/null; then
        echo "Ollama 进程异常退出，即将重启..."
        ollama serve &
    fi
    sleep 30
done