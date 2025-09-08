#!/bin/bash

# Check if the file path argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <output_dir>"
    exit 1
fi

OUTPUT_DIR=$1

MAPFILE_PATH=$1 + "/mapfile.ot"

# Run the octomap_saver command with the provided file path
rosrun octomap_server octomap_saver -f "$MAPFILE_PATH"
sleep 3s

# save pose to file
rosservice call /save_pose "destination: '$OUTPUT_DIR'" 
sleep 2s

# save global cloud map to file
rosservice call /save_map "{'resolution': 0.1, 'destination': '$OUTPUT_DIR'}"
