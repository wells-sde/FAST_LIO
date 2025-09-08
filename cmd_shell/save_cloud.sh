#!/bin/bash

# Check if the file path argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <output_dir>"
    exit 1
fi

OUTPUT_DIR=$1

# save global cloud map to file
rosservice call /save_map "{'resolution': 0.1, 'destination': '$OUTPUT_DIR'}"