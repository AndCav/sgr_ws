#!/usr/bin/python

import rospy
from std_msgs.msg           import Int32
from geometry_msgs.msg      import Twist
from math                   import radians
from tf.transformations     import quaternion_from_euler

class Thief():

    move_cmd = Twist()
    last_gesture = 0
    actual_gesture = 0
    forward = 5
    right = 3
    left = 2
    stop = 4
    idk = 0
    lin_vel = 0.2
    ang_vel = 60

    def __init__ (self):
        rospy.loginfo("Starting Thief")
        rospy.init_node('thief', anonymous=True)

        topic_robot = "/tb3_0"
        topic_vel = topic_robot + '/cmd_vel'

        self.cmd_vel = rospy.Publisher(topic_vel, Twist, queue_size=10)
        self.gesture = rospy.Subscriber("/gesture_channel", Int32, self.callback)

        self.rate = rospy.Rate(500)
    # End Init


    def callback(self, data):
        self.actual_gesture = data.data
        #rospy.loginfo("comando -> %s", self.actual_gesture)

        '''
        self.move_cmd.linear.x=0.5 #0.5 m/s
        self.move_cmd.angular.z = radians(45) #45 deg/s
        self.cmd_vel.publish(self.move_cmd)
        self.rate.sleep()
        '''

        if self.actual_gesture != self.last_gesture:
            rospy.loginfo("comando -> %s", self.actual_gesture)
            if self.actual_gesture == self.stop :
                self.move_cmd.linear.x = 0
                self.move_cmd.angular.z = 0

            elif self.actual_gesture == self.forward:
                self.move_cmd.linear.x = self.lin_vel
                self.move_cmd.angular.z = 0

            elif self.move_cmd.linear!=0 and self.actual_gesture == self.right:
                self.move_cmd.linear.x = self.lin_vel
                self.move_cmd.angular.z = -radians(self.ang_vel)
            
            elif self.move_cmd.linear!=0 and self.actual_gesture == self.left:
                self.move_cmd.linear.x = self.lin_vel
                self.move_cmd.angular.z = radians(self.ang_vel)

            elif self.actual_gesture == self.right and self.move_cmd.linear==0:
                self.move_cmd.linear.x = 0
                self.move_cmd.angular.z = -radians(self.ang_vel)
            
            elif self.actual_gesture == self.left and self.move_cmd.linear==0:
                self.move_cmd.linear.x = 0
                self.move_cmd.angular.z = radians(self.ang_vel)

        self.last_gesture = self.actual_gesture
        self.cmd_vel.publish(self.move_cmd)
        self.rate.sleep()
    # End Callback
# End Class


''' 
def behaviour():
    rospy.init_node('behaviour', anonymous=True)

    rospy.Subscriber("/gesture_channel", Int32, callback)

    # spin() simply keeps python from exiting until this node is stopped
    rospy.spin()
'''

if __name__ == '__main__':
    try:
        Thief()
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo("GAME OVER")