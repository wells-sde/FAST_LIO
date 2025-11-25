#!/bin/bash

# Check if the file path argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <output_dir>"
    exit 1
fi

OUTPUT_DIR=$1
MAPFILE_PATH="${OUTPUT_DIR}/mapfile.ot"
mkdir -p "$OUTPUT_DIR"

# 获取当前文件夹的绝对路径
SCRIPT_DIR=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")

# ros workspace 根目录
ROS_WORKSPACE_DIR=$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")
echo "ROS_WORKSPACE_DIR: $ROS_WORKSPACE_DIR"

source "$ROS_WORKSPACE_DIR/devel/setup.bash"

# Run the octomap_saver command with the provided file path
rosrun octomap_server octomap_saver -f "$MAPFILE_PATH"
sleep 3s

# save pose to file
rosservice call /save_pose "destination: '$OUTPUT_DIR'" 
sleep 2s

# save global cloud map to file
rosservice call /save_map "{'resolution': 0.1, 'destination': '$OUTPUT_DIR'}"
