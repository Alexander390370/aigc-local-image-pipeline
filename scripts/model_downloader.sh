#!/bin/bash
# Download community models from hf-mirror.com
set -e
TARGET=~/stable-diffusion-webui-forge/models/Stable-diffusion
mkdir -p "$TARGET"
cd "$TARGET"

aria2c -x 16 -s 16 -c \
  "https://hf-mirror.com/scenario-labs/Realistic_Vision_V5.1_noVAE/resolve/main/Realistic_Vision_V5.1.safetensors"

echo "Done. Models in $TARGET"
