#!/usr/bin/env sh

#设置为实际的ros workspace根目录
WORK_DIR=$(dirname "$(dirname "$(pwd)")")

# 启动SLAM
gnome-terminal -t "LIO" --working-directory="$WORK_DIR"  -- bash -c  "source ./devel/setup.bash;roslaunch fast_lio mapping_unitree_G1.launch;exec bash;"
sleep 2s

# 启动Lidar
gnome-terminal -t "Livox driver" --working-directory="$WORK_DIR"  -- bash -c  "source ./devel/setup.bash;roslaunch livox_ros_driver2 msg_MID360.launch;exec bash;"
sleep 2s

# 启动OctoMapping
gnome-terminal -t "octo_mapping" --working-directory="$WORK_DIR"  -- bash -c  "source ./devel/setup.bash;roslaunch fast_lio octo_mapping.launch;exec bash;"
