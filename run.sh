#!/bin/bash

# Fetch the latest changes from the remote repository
git pull origin main

# Fetch is blocking, so the script will wait until it's done

# Run the main.py file
./main.py