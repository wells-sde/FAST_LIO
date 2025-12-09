#!/bin/bash

# 获取当前文件夹的绝对路径
SCRIPT_DIR=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")

# ros workspace 根目录
LIO_WS_DIR=$(dirname "$(dirname "$SCRIPT_DIR")")

# 设置为实际的livox lidar driver 根目录
LIDAR_DRIVER_DIR=$LIO_WS_DIR

echo "lio workspace dir: $LIO_WS_DIR"
echo "livox lidar driver dir: $LIDAR_DRIVER_DIR"

# 启动SLAM
gnome-terminal -t "LIO" --working-directory="$LIO_WS_DIR"  -- bash -c  "source ./devel/setup.bash;roslaunch fast_lio mapping_go2w.launch;exec bash;"
sleep 2s

# 启动OctoMapping
gnome-terminal -t "octo_mapping" --working-directory="$LIO_WS_DIR"  -- bash -c  "source ./devel/setup.bash;roslaunch fast_lio octo_mapping_go2w.launch;exec bash;"
sleep 2s

# 启动Lidar
gnome-terminal -t "Livox driver" --working-directory="$LIDAR_DRIVER_DIR"  -- bash -c  "source ./devel/setup.bash;roslaunch livox_ros_driver2 msg_MID360.launch;exec bash;"
