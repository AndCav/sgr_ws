#!/usr/bin/python

import rospy
import sys
from geometry_msgs.msg      import Twist
from nav_msgs.msg           import Odometry
from sensor_msgs.msg        import LaserScan
from math                   import radians, atan2, isinf, fabs
from std_msgs.msg           import Int32

class Tb3Wonder():
    
    escape_range_ = radians(30)
    check_forward_dist_ = 0.6
    check_side_dist_ = 0.6
    
    tb3_pose_ = 0.0
    prev_tb3_pose_ = 0.0
    state = 0
    
    scan_data_ = [0.0, 0.0, 0.0]
    center = 0
    left = 1
    right = 2

    lin_vel = 0.5
    ang_vel = 0.5

    get_direction = 0
    drive_forward = 1
    turn_right = 2
    turn_left = 3

    error = 0
    ang_vel_error = 0
    gain = 0.003

    def __init__ (self):
        #rospy.loginfo("Starting Wonder 1")
        rospy.init_node('Wonder', anonymous=True)

        self.topic_robot = sys.argv[1]
        self.topic_vel = self.topic_robot + rospy.get_param("topic_vel")
        self.topic_odom= self.topic_robot +  rospy.get_param("topic_odom")
        self.topic_laser_scan = self.topic_robot +  rospy.get_param("topic_laser_scan")
        self.topic_error = self.topic_robot +  rospy.get_param("topic_error")

        self.cmd_vel = rospy.Publisher(self.topic_vel, Twist, queue_size=10)
        self.odom = rospy.Subscriber(self.topic_odom, Odometry, self.OdomCallback)
        self.laser_scan = rospy.Subscriber(self.topic_laser_scan, LaserScan, self.ScanCallback)
        self.error_scan = rospy.Subscriber(self.topic_error, Int32, self.ErrorCallback)
    # End Init

    def ScanCallback(self, data):
        scan_angle = [0, 30, 330]
        i = 0
        while i<len(scan_angle):
            if isinf(data.ranges[scan_angle[i]]):
                self.scan_data_[i] = data.range_max
            else :
                self.scan_data_[i] = data.ranges[scan_angle[i]]
            i = i+1
        self.ControlLoop()
    #End ScanCallback
    
    def OdomCallback(self, data):
        siny = 2 * (data.pose.pose.orientation.w * data.pose.pose.orientation.z + data.pose.pose.orientation.x * data.pose.pose.orientation.y)
        cosy = 1.0 - 2.0 * (data.pose.pose.orientation.y * data.pose.pose.orientation.y + data.pose.pose.orientation.z * data.pose.pose.orientation.z)
        self.tb3_pose_ = atan2(siny, cosy)
    # End OdomCallback

    def ErrorCallback (self, data):
        self.error = data.data
        self.ang_vel_error = self.gain * self.error
    #End ErrorCallback

    def ControlLoop (self):
        rospy.loginfo("ctr_loop: %s", self.scan_data_)
        rate = rospy.Rate(500)
        a_error = abs(self.error)

        if a_error > 1:
            self.UpdateVelocity(self.lin_vel, self.ang_vel_error)
        else:
            self.Wonder()

        rate.sleep()
    # End Control Loop

    def Wonder(self):

        if self.state == self.get_direction:
            if self.scan_data_[self.center] > self.check_forward_dist_:
                if self.scan_data_[self.left] < self.check_side_dist_:
                    self.prev_tb3_pose_ = self.tb3_pose_
                    self.state = self.turn_right
                elif self.scan_data_[self.right] < self.check_side_dist_:
                    self.prev_tb3_pose_ = self.tb3_pose_
                    self.state = self.turn_left
                else:
                    self.state = self.drive_forward
            
            if self.scan_data_[self.center] < self.check_forward_dist_:
                self.prev_tb3_pose_ = self.tb3_pose_
                self.state = self.turn_right
        
        elif self.state == self.drive_forward:
            self.UpdateVelocity(self.lin_vel, 0.0)
            self.state = self.get_direction

        elif self.state == self.turn_right:
            if (fabs(self.prev_tb3_pose_ - self.tb3_pose_) >= self.escape_range_):
                self.state = self.get_direction
            else:
                self.UpdateVelocity(0.0, -1*self.ang_vel)

        elif self.state == self.turn_left:
            if (fabs(self.prev_tb3_pose_ - self.tb3_pose_) >= self.escape_range_):
                self.state = self.get_direction
            else:
                self.UpdateVelocity(0.0, self.ang_vel)
        
        else:
            self.state = self.get_direction

    # End Wonder

    def UpdateVelocity (self, lin, ang):
        cmd_twist = Twist()
        cmd_twist.linear.x = lin
        cmd_twist.angular.z = ang
        self.cmd_vel.publish(cmd_twist)
    # End UpdateVelocity

#End Class



if __name__ == '__main__':
    try:
        tb = Tb3Wonder()

        while not rospy.is_shutdown():
            #tb.ControlLoop()
            rospy.spin()
            
            
    except rospy.ROSInterruptException:
        rospy.loginfo("GAME OVER")
        pass