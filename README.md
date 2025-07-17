## 1. Prerequisites
ROS, PCL, Eigen, [livox_ros_driver2](https://github.com/Livox-SDK/livox_ros_driver2), [octomap_server](http://wiki.ros.org/octomap_server)

## 2. Build
Clone the repository and catkin_make:

```
    cd ~/slam_ws/src
    git clone xxxx
    cd LI_SLAM
    git submodule update --init
    cd ../..
    catkin_make
    source devel/setup.bash
```
##  3. Run
请在机器人静止不动时启动li_slam，启动后slam会进行imu初始化，初始化完（几百ms）即可控制机器人运动
3.1 运行lidar slam
```shell
    cd ~/my_slam
    source devel/setup.bash
    #lio
    roslaunch fast_lio mapping_mid360.launch
    # LIDAR driver
    roslaunch livox_ros_driver2 msg_MID360.launch
```
3.2 运行octo_mapping在线建图，建图结束后可保存地图文件，详见[保存地图](doc/pointcloud_to_map.md)
```shell
roslaunch fast_lio octo_mapping.launch
#保存一个完整的概率八叉树地图
rosrun octomap_server octomap_saver -f mapfile.ot

#保存2D栅格地图
rosrun map_server map_saver -f mymap
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
