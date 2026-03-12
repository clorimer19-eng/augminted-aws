#!/bin/bash
echo "=== Augminted Cloud Setup ==="
echo "Fixing permissions for Google Cloud SDK..."

SDK_PATH="$HOME/Downloads/google-cloud-sdk"

# 1. Clear Quarantine
xattr -r -d com.apple.quarantine "$SDK_PATH" 2>/dev/null
echo "Quarantine attribute cleared (if present)."

# 2. Run Install (if needed)
if [ ! -f "$SDK_PATH/bin/gcloud" ]; then
    echo "gcloud binary not found at $SDK_PATH/bin/gcloud"
    echo "Please ensure you extracted the SDK to Downloads."
    exit 1
fi

# 3. Auth Login
echo "Launching Google Cloud Login..."
"$SDK_PATH/bin/gcloud" auth login

# 4. Set Project
echo "Setting project to 'augminted'..."
"$SDK_PATH/bin/gcloud" config set project augminted

echo "=== Setup Complete ==="
echo "You can now ask the AI to proceed with deployment."
