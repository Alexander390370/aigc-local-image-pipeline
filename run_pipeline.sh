#!/bin/bash
cd ~/aigc-local-image-pipeline
conda activate sd-forge

# Wait for Forge API to be ready
echo "Waiting for Forge API at http://127.0.0.1:7860 ..."
for i in {1..60}; do
    if curl -s http://127.0.0.1:7860/sdapi/v1/sd-models > /dev/null 2>&1; then
        echo "Forge API is ready."
        break
    fi
    sleep 2
done

# Run batch generation
mkdir -p /mnt/c/Users/34246/Desktop/aigc-output
python scripts/batch_gen.py \
  --prompts prompts/examples.txt \
  --output /mnt/c/Users/34246/Desktop/aigc-output

echo "Done. Output in ~/Desktop/aigc-output"
