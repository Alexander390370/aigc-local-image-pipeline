#!/bin/bash
# Wait for Forge API to be ready, then run batch generation.
# Output goes to $AIGC_OUTPUT if set, else ~/generated.

set -e

if ! command -v conda >/dev/null 2>&1; then
    echo "Error: conda not found on PATH. Install Miniconda or source conda.sh first." >&2
    exit 1
fi

source "$(conda info --base)/etc/profile.d/conda.sh"
if ! conda activate sd-forge; then
    echo "Error: failed to activate conda env 'sd-forge'." >&2
    exit 1
fi

cd "$(dirname "$0")"

OUTPUT_DIR="${AIGC_OUTPUT:-$HOME/generated}"
mkdir -p "$OUTPUT_DIR"

echo "Waiting for Forge API at http://127.0.0.1:7860 ..."
READY=0
for i in {1..60}; do
    if curl -s http://127.0.0.1:7860/sdapi/v1/sd-models > /dev/null 2>&1; then
        echo "Forge API is ready."
        READY=1
        break
    fi
    sleep 2
done

if [ "$READY" -ne 1 ]; then
    echo "Error: Forge API did not respond within 120 seconds." >&2
    exit 1
fi

python scripts/batch_gen.py \
  --prompts prompts/examples.txt \
  --output "$OUTPUT_DIR"

echo "Done. Output in $OUTPUT_DIR"
