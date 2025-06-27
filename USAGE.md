##  Run
运行lidar slam
```shell
    cd ~/my_slam
    source devel/setup.bash
    #lio
    roslaunch fast_lio mapping_mid360.launch
    # LIDAR driver
    roslaunch livox_ros_driver2 msg_MID360.launch
```
运行octomapping在线建图，建图结束后可保存地图文件，详见[保存地图](doc/pointcloud_to_map.md)
```shell
roslaunch fast_lio octo_mapping.launch
#保存一个完整的概率八叉树地图
rosrun octomap_server octomap_saver -f mapfile.ot

#保存2D栅格地图
rosrun map_server map_saver -f mymap
```