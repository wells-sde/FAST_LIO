#!/bin/bash

# Check if the file path argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <mapfile_path>"
    exit 1
fi

# Get the file path(*.ot) from the command line argument
MAPFILE_PATH=$1

# Run the octomap_saver command with the provided file path
rosrun octomap_server octomap_saver -f "$MAPFILE_PATH"