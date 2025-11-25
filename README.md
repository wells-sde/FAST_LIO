## 1. Prerequisites
ROS, PCL, Eigen, [livox_ros_driver2](https://github.com/Livox-SDK/livox_ros_driver2), [octomap_server](http://wiki.ros.org/octomap_server), [GTSAM>4.0.0](https://gtsam.org/get_started/),  [GeographicLib](https://github.com/geographiclib/geographiclib/tree/release), [Open3D](https://www.open3d.org/docs/release/getting_started.html), ros_numpy

## 2. Build
Clone the repository and catkin_make:

```shell
    mkdir -p ~/slam_ws/src && cd ~/slam_ws/src
    git clone xxxx
    cd LI_SLAM
    git submodule update --init
    cd ../..
    source livox_ros_driver2_workspace/devel/setup.bash
    catkin_make
    source devel/setup.bash
```
##  3. Run
请在机器人静止不动时启动li_slam，启动后slam会进行imu初始化，初始化完（几百ms）即可控制机器人运动。

### 3.1 运行lidar slam 建图模式

+ 方式1： 通过脚本运行

将lio_mapping.sh中的 `LIDAR_DRIVER_DIR` 和 `LIO_WS_DIR` 替换为实际LIDAR驱动的work space和LI_SLAM的work space路径, 运行：

`./lio_mapping.sh`

+ 方式2： 通过命令行运行
```shell
    cd ~/my_slam
    source devel/setup.bash
    #lio
    roslaunch fast_lio mapping_mid360.launch
    # LIDAR driver
    roslaunch livox_ros_driver2 msg_MID360.launch
    # 运行octo_mapping在线建图
    roslaunch fast_lio octo_mapping.launch
```
### 3.2 建图结束后保存地图文件

+ 方式1： 使用脚本 

`./cmd_shell/save_map_and_pose.sh  your_output_dir` 

保存octomap体素地图、3D点云地图及关键帧轨迹。输出目录使用绝对路径。

+ 方式2：使用以下命令（详见[保存地图](doc/pointcloud_to_map.md)）：

```shell
#保存一个完整的概率八叉树地图
rosrun octomap_server octomap_saver -f mapfile.ot

#保存2D栅格地图
rosrun map_server map_saver -f mymap

#保存3D点云地图到给定的目录
rosservice call /save_map "{'resolution': 0.1, 'destination': 'change_to_your_output_directory'}"

#保存关键帧轨迹到给定的目录
rosservice call /save_pose "destination: 'change_to_your_output_directory'" 
```

### 3.3 远程可视化
在用于显示的电脑上配置ROS环境：
```shell
#机器人ip地址
export ROS_MASTER_URI=http://192.168.123.164:11311
#本机局域网ip地址
export ROS_IP=192.168.0.44
#文件可从rviz_cfg/目录下拷贝
rviz -d lio_map.rviz
```

### 3.4 运行SLAM定位模式

+ 方式1： 通过脚本运行

将lio_loc.sh中的 `LIDAR_DRIVER_DIR` 和 `LIO_WS_DIR` 替换为实际LIDAR驱动的work space和LI_SLAM的work space路径。

先`conda deactivate`退出conda，进入系统环境，然后运行：

`./lio_loc.sh  path_to_filterGlobalMap.pcd`

地图加载显示后，在rviz中使用2D Pose Estimate功能设置机器人相对于地图的初始位置。

+ 方式2： 通过命令行运行
```shell
#运行slam定位模式,提供点云地图文件
roslaunch fast_lio localization_unitree_G1.launch map_file:=filterGlobalMap.pcd

# LIDAR driver
roslaunch livox_ros_driver2 msg_MID360.launch

#提供机器人相对地图坐标原点的初始位置
# x y z yaw pitch roll
rosrun fast_lio publish_initial_pose.py 0 0 0 0 0 0

# 也可以在rviz中使用2D Pose Estimate功能设置初始位置

```