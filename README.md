## 1. Prerequisites
ROS, PCL, Eigen, [livox_ros_driver2](https://github.com/Livox-SDK/livox_ros_driver2), [octomap_server](http://wiki.ros.org/octomap_server), [GeographicLib](https://github.com/geographiclib/geographiclib/tree/release), [Open3D](https://github.com/isl-org/Open3D)

## 2. Build
Clone the repository and catkin_make:

```
    cd ~/slam_ws/src
    git clone xxxx
    cd LI_SLAM
    git submodule update --init
    cd ../..
    source livox_ros_driver2_workspace/devel/setup.bash
    catkin_make
    source devel/setup.bash
```
##  3. Run
请在机器人静止不动时启动li_slam，启动后slam会进行imu初始化，初始化完（几百ms）即可控制机器人运动
3.1 运行lidar slam 建图模式
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
3.2 建图结束后保存地图文件，详见[保存地图](doc/pointcloud_to_map.md)
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

3.3 远程可视化
```shell
#机器人ip地址
export ROS_MASTER_URI=http://192.168.123.164:11311
#本机局域网ip地址
export ROS_IP=192.168.0.44
#文件可从rviz_cfg/目录下拷贝
rviz -d lio_map.rviz
```

3.4 运行SLAM定位模式
```shell
#运行slam定位模式,提供点云地图文件
roslaunch fast_lio locallization_unitree_G1.launch map_file:=filterGlobalMap.pcd
```