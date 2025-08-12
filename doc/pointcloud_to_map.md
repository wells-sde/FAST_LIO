从三维点云离线构建2D占据栅格地图、3D体素地图的流程

1. 发布点云

``` shell
#每隔2s 发布一次， 话题为/cloud_pcd，frmae_id为 map
rosrun pcl_ros pcd_to_pointcloud  cloud.pcd 2 _frame_id:=camera_init cloud_pcd:=/cloud_in

#如果坐标系需要变换，命令发布tf2
# x y z qx qy qz qw
rosrun tf2_ros static_transform_publisher 0 0 0 0.707 0 0 0.707 camera_init map

```

2. 启动octomap_server,订阅点云转换成3D体素并投影成2D占据珊格

```shell
roslaunch fast_lio pointcloud_to_map.launch
```

3. 保存占据2D栅格地图、3D体素地图

```shell
#保存压缩的二进制存储格式占据八叉树地图
rosrun octomap_server octomap_saver mapfile.bt
#保存一个完整的概率八叉树地图
rosrun octomap_server octomap_saver -f mapfile.ot

#保存2D栅格地图
rosrun map_server map_saver -f mymap

```
4. 读取体素地图文件，显示、发布
```shell
#通过octovis显示地图文件
#sudo apt-get install octovis
octovis xxx.ot[bt]

#通过ros话题发布地图 /octomap_binary， /octomap_full，/occupied_cells_vis_array 
#rosrun octomap_server octomap_server_node map_file:=/home/airs/sim_single_box _frame_id:=camera_init

#或者通过roslaunch 启动
roslaunch fast_lio load_octomap.launch
```