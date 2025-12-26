#!/usr/bin/env python3
# coding=utf8
from __future__ import print_function, division, absolute_import

import copy
import threading
import time
import math

import open3d as o3d
import rospy
import ros_numpy
from geometry_msgs.msg import PoseWithCovarianceStamped, Pose, Point, Quaternion
from nav_msgs.msg import Odometry
from sensor_msgs.msg import PointCloud2
import numpy as np
import tf
import tf.transformations

global_map = None
initialized = False
T_map_to_odom = np.eye(4)
cur_odom = None
cur_scan = None
cur_timestamp = None
last_timestamp = -1.0

USE_ICP_PLANE_TO_PLANE = False
MAX_ITERATION = 30
INITIAL_MAX_ITERATION = 50

need_global_loc=True
last_success_pose = None
first_success_time = None
moved_distance = 0.0
last_t_map_to_odom = None


def pose_to_mat(pose_msg):
    return np.matmul(
        tf.listener.xyz_to_mat44(pose_msg.pose.pose.position),
        tf.listener.xyzw_to_mat44(pose_msg.pose.pose.orientation),
    )


def msg_to_array(pc_msg):
    pc_array = ros_numpy.numpify(pc_msg)
    pc = np.zeros([len(pc_array), 3])
    pc[:, 0] = pc_array['x']
    pc[:, 1] = pc_array['y']
    pc[:, 2] = pc_array['z']
    #intensity
    # pc[:, 3] = pc_array['intensity']
    return pc


def registration_at_scale(pc_scan, pc_map, initial, scale, max_distance=1.0, max_iter=30):
    result_icp = o3d.pipelines.registration.registration_icp(
        voxel_down_sample(pc_scan, SCAN_VOXEL_SIZE * scale), voxel_down_sample(pc_map, MAP_VOXEL_SIZE * scale),
        max_distance* scale, initial,
        o3d.pipelines.registration.TransformationEstimationPointToPoint(),
        o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=max_iter)
    )

    return result_icp.transformation, result_icp.fitness, result_icp.inlier_rmse

def registration_gicp(pc_scan, pc_map, initial, max_distance=1.0, max_iter=30):
    pc_scan_down = voxel_down_sample(pc_scan, SCAN_VOXEL_SIZE)
    pc_scan_down.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=SCAN_VOXEL_SIZE*2.0, max_nn=30))
    
    # gicp
    reg = o3d.pipelines.registration.registration_generalized_icp(
        pc_scan_down, pc_map, max_distance, initial,
        o3d.pipelines.registration.TransformationEstimationForGeneralizedICP(),
        o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=max_iter)
    )
    return reg.transformation, reg.fitness, reg.inlier_rmse

def inverse_se3(trans):
    trans_inverse = np.eye(4)
    # R
    trans_inverse[:3, :3] = trans[:3, :3].T
    # t
    trans_inverse[:3, 3] = -np.matmul(trans[:3, :3].T, trans[:3, 3])
    return trans_inverse


def publish_point_cloud(publisher, header, pc):
    data = np.zeros(len(pc), dtype=[
        ('x', np.float32),
        ('y', np.float32),
        ('z', np.float32),
        ('intensity', np.float32),
    ])
    data['x'] = pc[:, 0]
    data['y'] = pc[:, 1]
    data['z'] = pc[:, 2]
    if pc.shape[1] == 4:
        data['intensity'] = pc[:, 3]
    msg = ros_numpy.msgify(PointCloud2, data)
    msg.header = header
    publisher.publish(msg)


def crop_global_map_in_FOV(global_map, pose_estimation, cur_odom):
    # 当前scan原点的位姿
    # pose_estimation是T_map_to_odom,即机器人起始位置在map系下的位姿
    T_odom_to_base_link = pose_to_mat(cur_odom)
    T_map_to_base_link = np.matmul(pose_estimation, T_odom_to_base_link)
    # # pose_estimation 为当前机器人位姿在map系下的估计
    # T_map_to_base_link = pose_estimation
    T_base_link_to_map = inverse_se3(T_map_to_base_link)

    # 把地图转换到lidar系下
    global_map_in_map = np.array(global_map.points)
    global_map_in_map = np.column_stack([global_map_in_map, np.ones(len(global_map_in_map))])
    global_map_in_base_link = np.matmul(T_base_link_to_map, global_map_in_map.T).T

    # rotate normals if using plane to plane icp
    if USE_ICP_PLANE_TO_PLANE:
        global_map_in_map_normals = np.array(global_map.normals)
        R_map_to_base_link = T_base_link_to_map[:3, :3]
        global_map_in_base_link_normals = np.matmul(R_map_to_base_link, global_map_in_map_normals.T).T
        global_map_in_base_link = np.column_stack([global_map_in_base_link[:, :3], global_map_in_base_link_normals, np.ones(len(global_map_in_base_link))])


    # 将视角内的地图点提取出来
    if FOV > 3.14:
        # 环状lidar 仅过滤距离
        indices = np.where(
            (np.sqrt(global_map_in_base_link[:, 0]**2 + global_map_in_base_link[:, 1]**2 + global_map_in_base_link[:, 2]**2) < FOV_FAR)
        )
    else:
        # 非环状lidar 保前视范围
        # FOV_FAR>x>0 且角度小于FOV
        indices = np.where(
            (global_map_in_base_link[:, 0] > 0) &
            (np.sqrt(global_map_in_base_link[:, 0]**2 + global_map_in_base_link[:, 1]**2 + global_map_in_base_link[:, 2]**2) < FOV_FAR) &
            (np.abs(np.arctan2(global_map_in_base_link[:, 1], global_map_in_base_link[:, 0])) < FOV / 2.0)
        )
    global_map_in_FOV = o3d.geometry.PointCloud()
    global_map_in_FOV.points = o3d.utility.Vector3dVector(np.squeeze(global_map_in_map[indices, :3]))

    if USE_ICP_PLANE_TO_PLANE:
        global_map_in_FOV.normals = o3d.utility.Vector3dVector(np.squeeze(global_map_in_base_link[indices, 3:6]))

    # 发布fov内点云
    header = cur_odom.header
    header.frame_id = 'map'
    publish_point_cloud(pub_submap, header, np.array(global_map_in_FOV.points)[::10])

    return global_map_in_FOV


def global_localization(pose_estimation):
    global global_map, cur_scan, cur_odom, T_map_to_odom, last_timestamp, initialized
    global need_global_loc,first_success_time, last_success_pose, last_t_map_to_odom, moved_distance

    last_timestamp = cur_odom.header.stamp.to_sec()
    # TODO 这里注意线程安全
    scan_tobe_mapped = copy.copy(cur_scan)

    # todo
    #检查cur_scan 和cur_odom的时间是否一致

    tic = time.time()

    global_map_in_FOV = crop_global_map_in_FOV(global_map, pose_estimation, cur_odom)

    # 粗配准
    # transformation, _ = registration_at_scale(scan_tobe_mapped, global_map_in_FOV, initial=pose_estimation, scale=5)

    # 精配准
    # transformation, fitness = registration_at_scale(scan_tobe_mapped, global_map_in_FOV, initial=transformation,
    #                                                 scale=1)

    if initialized is False:
        max_iteration = INITIAL_MAX_ITERATION
    else:
        max_iteration = MAX_ITERATION

    if USE_ICP_PLANE_TO_PLANE:
        transformation, fitness, rmse = registration_gicp(scan_tobe_mapped, global_map_in_FOV, initial=pose_estimation,
                                                    max_distance=1.0, max_iter=max_iteration)
    else:
        transformation, fitness, rmse = registration_at_scale(scan_tobe_mapped, global_map_in_FOV, initial=pose_estimation,
                                                    max_distance=1.0, scale=1, max_iter=max_iteration)
    toc = time.time()
    rospy.logdebug('Cost of Time of Global Register: {}s'.format(toc - tic))

    # 当全局定位成功时才更新map2odom
    if fitness > LOCALIZATION_TH:
        # T_map_to_odom = np.matmul(transformation, pose_estimation)
        T_map_to_odom = transformation

        # 发布map_to_odom
        map_to_odom = Odometry()
        xyz = tf.transformations.translation_from_matrix(T_map_to_odom)
        quat = tf.transformations.quaternion_from_matrix(T_map_to_odom)
        map_to_odom.pose.pose = Pose(Point(*xyz), Quaternion(*quat))
        map_to_odom.header.stamp = cur_odom.header.stamp
        map_to_odom.header.frame_id = 'map'
        pub_map_to_odom.publish(map_to_odom)
        euler = tf.transformations.euler_from_quaternion(quat)
        rospy.loginfo('frame {}, global localization success!!!!'.format(last_timestamp))
        rospy.loginfo('x y z, roll pitch yaw:{} {}'.format(xyz, euler))
        rospy.loginfo('fitness score:{}, inlier rmse: {}'.format(fitness, rmse))

        if initialized is False:
            last_success_pose = cur_odom.pose.pose.position
            first_success_time = cur_odom.header.stamp.to_sec()
            last_t_map_to_odom = copy.copy(T_map_to_odom)
        else:
            # 如果已经初始化成功了, 但是map_to_odom变化很大，说明全局定位偏了
            # 计算T_map_to_odom和last_t_map_to_odom的差异   
            # delta_trans = np.linalg.norm(T_map_to_odom[:3, 3] - last_t_map_to_odom[:3, 3])
            # delta_rot = np.arccos(
            #     min(
            #         max(
            #             (np.trace(np.dot(T_map_to_odom[:3, :3], last_t_map_to_odom[:3, :3].T)) - 1) / 2.0,
            #             -1.0
            #         ),
            #         1.0
            #     )
            # )
            # if delta_trans > MAP_VOXEL_SIZE*1.5 or delta_rot > math.radians(5.0):
            #     rospy.logwarn('T_map_to_odom inconsitent. Delta translation: {:.4f} m, Delta rotation: {:.4f} rad'.format(delta_trans, delta_rot))
            #     return False
            
            # 更新last_t_map_to_odom
            last_t_map_to_odom = copy.copy(T_map_to_odom)

            # 已经初始化成功后 需要满足一定条件才认为收敛, 停止全局定位
            enough_time = cur_odom.header.stamp.to_sec() - first_success_time > 5.0/FREQ_LOCALIZATION
            cur_pos = np.array([cur_odom.pose.pose.position.x, cur_odom.pose.pose.position.y, cur_odom.pose.pose.position.z])
            last_pos = np.array([last_success_pose.x, last_success_pose.y, last_success_pose.z])
            moved_distance += np.linalg.norm(cur_pos - last_pos)
            enough_moved = moved_distance > 3.0
            converged = rmse < MAP_VOXEL_SIZE * 1.0 and fitness > 0.99
            if enough_time and enough_moved and converged:
                need_global_loc = False
                rospy.logwarn('Global localization converged!!!!!!Exit global localization thread.')

            last_success_pose = cur_odom.pose.pose.position
            rospy.logdebug('moved_distance:{}'.format(moved_distance))
            
        return True
    else:
        rospy.logwarn('frame {}, Not match!!!!'.format(last_timestamp))
        # rospy.logwarn('{}'.format(transformation))
        rospy.logwarn('fitness score:{}, inlier rmse: {}'.format(fitness, rmse))
        return False


def voxel_down_sample(pcd, voxel_size):
    try:
        pcd_down = pcd.voxel_down_sample(voxel_size)
    except:
        # for opend3d 0.7 or lower
        pcd_down = o3d.geometry.voxel_down_sample(pcd, voxel_size)
    return pcd_down


def initialize_global_map(pc_msg):
    global global_map

    global_map = o3d.geometry.PointCloud()
    global_map.points = o3d.utility.Vector3dVector(msg_to_array(pc_msg)[:, :3])
    global_map = voxel_down_sample(global_map, MAP_VOXEL_SIZE)
    if USE_ICP_PLANE_TO_PLANE:
        global_map.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=MAP_VOXEL_SIZE*2.0, max_nn=30))
    rospy.loginfo('Global map received.')

def load_global_map(pcd_path):
    global global_map

    global_map = o3d.io.read_point_cloud(pcd_path)
    global_map = voxel_down_sample(global_map, MAP_VOXEL_SIZE)
    rospy.loginfo('Global map loaded from pcd. points:{}'.format(global_map.points.shape))

def cb_save_cur_odom(odom_msg):
    global cur_odom, cur_timestamp
    cur_odom = odom_msg
    cur_timestamp = odom_msg.header.stamp.to_sec()


def cb_save_cur_scan(pc_msg):
    global cur_scan
    # 注意这里fastlio直接将scan转到odom系下了 不是lidar局部系
    # pc_msg.header.frame_id = 'world'
    # pc_msg.header.stamp = rospy.Time().now()
    # pub_pc_in_map.publish(pc_msg)

    # 转换为pcd
    # fastlio给的field有问题 处理一下
    pc_msg.fields = [pc_msg.fields[0], pc_msg.fields[1], pc_msg.fields[2],
                     pc_msg.fields[4], pc_msg.fields[5], pc_msg.fields[6],
                     pc_msg.fields[3], pc_msg.fields[7]]
    pc = msg_to_array(pc_msg)

    cur_scan = o3d.geometry.PointCloud()
    cur_scan.points = o3d.utility.Vector3dVector(pc[:, :3])


def thread_localization():
    global T_map_to_odom, cur_timestamp, last_timestamp, need_global_loc
    while need_global_loc:
        # 每隔一段时间进行全局定位
        rospy.sleep(1 / FREQ_LOCALIZATION)

        # 如果里程计有更新才进行全局定位
        if cur_timestamp is None or cur_timestamp - last_timestamp < 0.01:
            continue

        # TODO 由于这里Fast lio发布的scan是已经转换到odom系下了 所以每次全局定位的初始解就是上一次的map2odom 不需要再拿odom了
        global_localization(T_map_to_odom)


if __name__ == '__main__':
    # Read parameters from launch (try private then global namespace), with defaults
    MAP_VOXEL_SIZE = float(rospy.get_param('~filter_size_map', rospy.get_param('filter_size_map', 0.2)))
    SCAN_VOXEL_SIZE = float(rospy.get_param('~filter_size_surf', rospy.get_param('filter_size_surf', 0.2)))

    # Global localization frequency (Hz)
    FREQ_LOCALIZATION = float(rospy.get_param('~freq_global_loc', rospy.get_param('freq_global_loc', 1.0)))

    rospy.loginfo('MAP_VOXEL_SIZE: {}, SCAN_VOXEL_SIZE: {}, FREQ_LOCALIZATION: {}'.format(
        MAP_VOXEL_SIZE, SCAN_VOXEL_SIZE, FREQ_LOCALIZATION))

    # The threshold of global localization,
    # only those scan2map-matching with higher fitness than LOCALIZATION_TH will be taken
    LOCALIZATION_TH = 0.9

    # FOV(rad), modify this according to your LiDAR type
    FOV = 2*math.pi

    # The farthest distance(meters) within FOV
    FOV_FAR = 70
    print('FOV is set to {} rad, max distance is set to {} m'.format(FOV, FOV_FAR))

    initial_pose = None

    rospy.init_node('global_localization')
    rospy.loginfo('Global Localization Node Inited...')

    # publisher
    # pub_pc_in_map = rospy.Publisher('/cur_scan_in_map', PointCloud2, queue_size=1)
    pub_submap = rospy.Publisher('/submap', PointCloud2, queue_size=1)
    pub_map_to_odom = rospy.Publisher('/map_to_odom', Odometry, queue_size=1)

    rospy.Subscriber('/cloud_registered', PointCloud2, cb_save_cur_scan, queue_size=1)
    rospy.Subscriber('/lidar_pose', Odometry, cb_save_cur_odom, queue_size=1)

    # 初始化全局地图
    rospy.logwarn('Waiting for global map......')
    initialize_global_map(rospy.wait_for_message('/cloud_map', PointCloud2))

    # 初始化
    while not initialized:
        rospy.logwarn('Waiting for initial pose....')

        # 等待初始位姿
        pose_msg = rospy.wait_for_message('/initialpose', PoseWithCovarianceStamped)
        initial_pose = pose_to_mat(pose_msg)
        if cur_scan is not None and cur_odom is not None:
            initialized = global_localization(initial_pose)
        else:
            rospy.logwarn('First scan not received!!!!!')

    rospy.loginfo('')
    rospy.loginfo('Initialize successfully!!!!!!')
    rospy.loginfo('')
    # 开始定期全局定位
    localization_thread = threading.Thread(target=thread_localization)
    localization_thread.daemon = True
    localization_thread.start()

    rospy.spin()
