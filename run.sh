#!/bin/bash

# Determine the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Fetch the latest changes from the remote repository
git -C "$SCRIPT_DIR" fetch origin main

# Fetch is blocking, so the script will wait until it's done

# Run the main.py file
"$SCRIPT_DIR/main.py"