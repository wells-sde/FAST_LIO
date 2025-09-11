#!/usr/bin/sh

# Check if the file path argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <pcd_path>"
    exit 1
fi


#设置为实际的ros workspace根目录
WORK_DIR=$(dirname "$(dirname "$(pwd)")")

#预建点云地图文件路径 filterGlobalMap.pcd
MAPFILE_PATH=$1

# 启动SLAM
gnome-terminal -t "LIO" --working-directory="$WORK_DIR"  -- bash -c  "source ./devel/setup.bash;roslaunch fast_lio localization_unitree_G1.launch map_file:=$MAPFILE_PATH;exec bash;"
sleep 3s

# 启动Lidar
gnome-terminal -t "Livox driver" --working-directory="$WORK_DIR"  -- bash -c  "source ./devel/setup.bash;roslaunch livox_ros_driver2 msg_MID360.launch;exec bash;"
