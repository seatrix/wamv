#! /usr/bin/env python

import rospy
import tf
import tf2_ros
import math
import message_filters
from geometry_msgs.msg import Twist, Quaternion, Vector3
from sensor_msgs.msg import Imu
from nav_msgs.msg import Odometry

###############################################################################
class OdometryPublisher():

    ###########################################################################
    def __init__(self):
        # Initialize node
        rospy.init_node('imu_odometry_estimation', log_level=rospy.INFO)

        # Get parameters
        # self.two_d_mode = rospy.get_param("~two_d_mode", False)

        # Set up subscribers
        message_filters.ApproximateTimeSynchronizer((
            message_filters.Subscriber('twist', Twist),
            message_filters.Subscriber('imu', Imu)),
            10, 0.1, allow_headerless=True
        ).registerCallback(self.callback)

        # Set up publisher
        self.odom_publisher = rospy.Publisher(
            'odom', Odometry, queue_size=10
        )

        # Set up listener
        self.buffer = tf2_ros.Buffer()
        self.listener = tf2_ros.TransformListener(self.buffer)


        # Initialize class variables
        self.odom = Odometry()
        self.odom.header.frame_id = rospy.get_param("~frame_id", "odom")
        self.odom.child_frame_id = rospy.get_param("~child_frame_id", "an_device")
        # self.odom.pose.pose.position.x = 0.0
        # self.odom.pose.pose.position.y = 0.0
        # self.odom.pose.pose.position.z = 0.0

        self.previous_time = None

    ###########################################################################
    def callback(self, twist_msg, imu_msg):
        """ TODO

            Twist in this message corresponds to the robot's velocity in the
            child frame, normally the coordinate frame of the mobile base,
            along with an optional covariance for the certainty of that
            velocity estimate.

            Pose in this message corresponds to the estimated position of the
            robot in the odometric frame along with an optional covariance for
            the certainty of that pose estimate.
        """
        current_time = imu_msg.header.stamp
        if self.previous_time is None:
            self.previous_time = current_time
            return

        self.odom.header.stamp = current_time
        self.odom.twist.twist.angular.x = twist_msg.angular.x
        self.odom.twist.twist.angular.y = twist_msg.angular.y
        self.odom.twist.twist.angular.z = twist_msg.angular.z

        quaternion = (
            imu_msg.orientation.x, imu_msg.orientation.y,
            imu_msg.orientation.z, imu_msg.orientation.w
        )

        # try:
        # transform = self.buffer.lookup_transform('base_link', 'imu', current_time)

        rotated = tf2_ros.quat_rotate(
            quaternion,
            (twist_msg.linear.x, twist_msg.linear.y, twist_msg.linear.z)
        )
        self.odom.twist.twist.linear.x = rotated[0]
        self.odom.twist.twist.linear.y = rotated[1]
        self.odom.twist.twist.linear.z = rotated[2]

        # except:
        #     pass


        self.odom.pose.pose.orientation = imu_msg.orientation

        ori = tf.transformations.euler_from_quaternion(quaternion)
        # quat = tf.transformations.quaternion_from_euler(0, 0, ori[2])
        # self.odom.pose.pose.orientation.x = quat[0]
        # self.odom.pose.pose.orientation.y = quat[1]
        # self.odom.pose.pose.orientation.z = quat[2]
        # self.odom.pose.pose.orientation.w = quat[3]

        theta = ori[2]

        # dt = (self.odom.header.stamp - self.previous_time).to_sec()
        # self.odom.pose.pose.position.x += dt * (
        #     self.odom.twist.twist.linear.x * math.cos(theta)
        #   - self.odom.twist.twist.linear.y * math.sin(theta)
        # )
        # self.odom.pose.pose.position.y += dt * (
        #     self.odom.twist.twist.linear.x * math.sin(theta)
        #   + self.odom.twist.twist.linear.y * math.cos(theta)
        # )
        # self.odom.pose.pose.position.z += dt * self.odom.twist.twist.linear.z

        self.odom_publisher.publish(self.odom)

        self.previous_time = self.odom.header.stamp

###############################################################################
###############################################################################
if __name__ == '__main__':
    try:
        odometry = OdometryPublisher()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
