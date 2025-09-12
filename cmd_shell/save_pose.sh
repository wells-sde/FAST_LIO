#!/bin/bash

# Check if the file path argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <output_dir>"
    exit 1
fi

OUTPUT_DIR=$1

# save pose to file
rosservice call /save_pose "destination: '$OUTPUT_DIR'" 