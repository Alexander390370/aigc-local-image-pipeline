#!/bin/bash
# Wait for Forge API to be ready, then run batch generation.
# Output goes to $AIGC_OUTPUT if set, else ~/generated.

source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null
conda activate sd-forge 2>/dev/null

cd "$(dirname "$0")"

OUTPUT_DIR="${AIGC_OUTPUT:-$HOME/generated}"
mkdir -p "$OUTPUT_DIR"

echo "Waiting for Forge API at http://127.0.0.1:7860 ..."
for i in {1..60}; do
    if curl -s http://127.0.0.1:7860/sdapi/v1/sd-models > /dev/null 2>&1; then
        echo "Forge API is ready."
        break
    fi
    sleep 2
done

python scripts/batch_gen.py \
  --prompts prompts/examples.txt \
  --output "$OUTPUT_DIR"

echo "Done. Output in $OUTPUT_DIR"
