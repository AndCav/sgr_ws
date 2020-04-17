#!/usr/bin/python

import rospy
import cv2
import sys

from std_msgs.msg           import String, Int32
from sensor_msgs.msg        import Image
from geometry_msgs.msg      import Point
from cv_bridge              import CvBridge, CvBridgeError
from geometry_msgs.msg      import Twist
import numpy                as np

class FollowRed:

    low_blue = np.array([94, 0, 0]) 
    high_blue = np.array([126, 255, 255])
    blur = 1
    center_std = (400, 400)

    def __init__ (self):
        rospy.init_node('Follow_blue_Tb3_1', anonymous=True)

        self.topic_robot = sys.argv[1]
        self.topic_cam = self.topic_robot + '/bot_camera/image_raw'
        self.topic_vel = self.topic_robot + rospy.get_param("topic_vel")
        self.topic_error = self.topic_robot +  rospy.get_param("topic_error")

        self.bridge = CvBridge()
        self.image_sub = rospy.Subscriber(self.topic_cam, Image, self.CamCallback)
        self.cmd_vel = rospy.Publisher(self.topic_vel, Twist, queue_size=10)
        self.error_pub = rospy.Publisher(self.topic_error, Int32, queue_size=10)

        pass
    
    def CamCallback (self, img):
        #--- Image is 800x800
        try:
            image = self.bridge.imgmsg_to_cv2(img, "bgr8")
        except CvBridgeError as e:
            print(e)
        
        center = self.BlobDetect(image, self.low_blue, self.high_blue, self.blur, None)
        error = self.center_std[0] - center[0]
        a_error = abs(error)
        self.error_pub.publish(error)

        rospy.loginfo("Center: %s", center)
        rospy.loginfo("Error: %s", error)

    # End cam_callback

    def BlobDetect(self,
                image,                  #-- The frame (cv standard)
                hsv_min,                #-- minimum threshold of the hsv filter [h_min, s_min, v_min]
                hsv_max,                #-- maximum threshold of the hsv filter [h_max, s_max, v_max]
                blur=0,                 #-- blur value (default 0)
                imshow=False
               ):

        
        value1 = (blur, blur)
        blurred = cv2.GaussianBlur(image, value1, 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        if imshow:
            cv2.imshow("Blur", blurred)
            cv2.waitKey(0)

        # Create a binary image with where white will be skin colors and rest is black
        mask = cv2.inRange(hsv, hsv_min, hsv_max) #Red

        if imshow:
            cv2.imshow("Mask", mask)
            cv2.waitKey(0)

        # Kernel for morphological transformation
        kernel = np.ones((5, 5))

        # Apply morphological transformations to filter out the background noise
        dilation = cv2.dilate(mask, kernel, iterations=1)
        erosion = cv2.erode(dilation, kernel, iterations=1)

        # Apply Gaussian Blur and Threshold
        value2 = (blur, blur)
        filtered = cv2.GaussianBlur(erosion, value2, 0)
        ret, thresh = cv2.threshold(filtered, 127, 255, 0)

        #Decommentare per detech del rosso
        #thresh = 255 - thresh

        # Find contours
        _, contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

        # Find contour with maximum area
        try:
            cnt = max(contours, key=lambda x: cv2.contourArea(x))
        


        #######################This line draws the center#####################
            moments = cv2.moments(cnt)
            if moments['m00']!=0:
                        cx = int(moments['m10']/moments['m00']) # cx = M10/M00
                        cy = int(moments['m01']/moments['m00']) # cy = M01/M00

            centr=(cx,cy)
            image = cv2.circle(image,centr,5,[0,255,0],2)
        ######################This line draws the center######################

            # Draw the contour
            hsv = cv2.drawContours(image, cnt, -1, (0, 255, 0), 2)

        except:
            centr = self.center_std
        
        cv2.imshow("Center", hsv)
        cv2.waitKey(3)

        return centr
    # End BlobDetect

    def UpdateVelocity (self, lin, ang):
        cmd_twist = Twist()
        cmd_twist.linear.x = lin
        cmd_twist.angular.z = ang
        self.cmd_vel.publish(cmd_twist)
    # End UpdateVelocity

if __name__ == '__main__':
    try:
        flwRed = FollowRed()
        while not rospy.is_shutdown():
            rospy.spin()

    except rospy.ROSInterruptException:
        rospy.loginfo("GAME OVER")