# 时间戳
std_msgs/Header header

# 枚举状态
uint8 state
# 状态枚举定义
uint8 NOT_INITIALIZED=0    # 还没完成初始化
uint8 ODOM_OK=1            # 定位正常
uint8 ODOM_BAD=2           # 定位精度较差
uint8 ODOM_DELAY=3         # 定位出现明显延迟
uint8 ODOM_FAILED=99       # 定位失败，不可用