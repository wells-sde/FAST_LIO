#!/bin/bash

# Check if the file path argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <pcd_path>"
    exit 1
fi

#预建点云地图文件路径 xxx/filterGlobalMap.pcd
MAPFILE_PATH=$1

# 获取当前文件夹的绝对路径
SCRIPT_DIR=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")

# slam workspace 根目录
LIO_WS_DIR=$(dirname "$(dirname "$SCRIPT_DIR")")

# livox lidar driver 根目录
LIDAR_DRIVER_DIR=$LIO_WS_DIR

echo "lio workspace dir: $LIO_WS_DIR"
echo "livox lidar driver dir: $LIDAR_DRIVER_DIR"

# 启动SLAM
gnome-terminal -t "LIO" --working-directory="$LIO_WS_DIR"  -- bash -c  "source ./devel/setup.bash;roslaunch fast_lio localization_unitree_G1.launch map_file:=$MAPFILE_PATH;exec bash;"
sleep 3s

# 启动Lidar
gnome-terminal -t "Livox driver" --working-directory="$LIDAR_DRIVER_DIR"  -- bash -c  "source ./devel/setup.bash;roslaunch livox_ros_driver2 msg_MID360.launch;exec bash;"
sleep 2s

# gnome-terminal -t "load octomap" --working-directory="$LIO_WS_DIR"  -- bash -c  "source ./devel/setup.bash;roslaunch fast_lio load_octomap.launch;exec bash;"
