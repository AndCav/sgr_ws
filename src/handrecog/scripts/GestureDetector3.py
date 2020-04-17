#!/usr/bin/python

import cv2
import math
import rospy
import numpy as np
from std_msgs.msg import String
from std_msgs.msg import Int32
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError

class GestureRecognizer:
    NODE_NAME = 'gesture_node'
    CX_INITIAL_VALUE = 0
    flag = True
    X = 0
    def __init__(self):
        self.cv_bridge = CvBridge()
        self.publisher = rospy.Publisher('/gesture_channel', Int32, queue_size=1)
        self.img_subscriber = rospy.Subscriber("/webcam_image", Image, self.callback)
        cv2.namedWindow("Gesture and Contour Window")
        self.rate = rospy.Rate(1000)

    def getInitialCx(self, cx):

        if GestureRecognizer.flag:
            GestureRecognizer.CX_INITIAL_VALUE = cx
            GestureRecognizer.flag = False

        return GestureRecognizer.CX_INITIAL_VALUE

    def callback(self, data):
        try:
            img = self.cv_bridge.imgmsg_to_cv2(data, "bgr8")  # Convert ROS image to CVMat
            
            init_point = (20,20)
            final_point = (320, 350)
            #cv2.rectangle(img,(2,10),(650,650),(0,255,0),5)
            cv2.rectangle(img,init_point,final_point,(0,255,0),3)
            #crop_img = img[2:650, 2:650]
            crop_img = img[20:350, 20:320]
            #crop_img = img

            #grey = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
            value1 = (15, 15)
            blurred = cv2.GaussianBlur(crop_img, value1, 0)
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

            # Create a binary image with where white will be skin colors and rest is black
            #mask = cv2.inRange(hsv, np.array([2, 0, 0]), np.array([20, 255, 255])) #Skin
            mask = cv2.inRange(hsv, np.array([94, 0, 0]), np.array([126, 255, 255])) #Blue

            # Kernel for morphological transformation
            kernel = np.ones((5, 5))

            # Apply morphological transformations to filter out the background noise
            dilation = cv2.dilate(mask, kernel, iterations=1)
            erosion = cv2.erode(dilation, kernel, iterations=1)

            # Apply Gaussian Blur and Threshold
            value2 = (13, 13)
            filtered = cv2.GaussianBlur(erosion, value2, 0)
            ret, thresh = cv2.threshold(filtered, 127, 255, 0)

            #_, thresh1 = cv2.threshold(blurred, 127, 255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
            # Find contours
            _, contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

            # Find contour with maximum area
            cnt = max(contours, key=lambda x: cv2.contourArea(x))

            '''
            max_area = -1
            for i in range(len(contours)):
                cnt=contours[i]
                area = cv2.contourArea(cnt)
                if(area>max_area):
                    max_area=area
                    ci=i
            cnt=contours[ci]
            '''

        #######################This line draws the center#####################
            moments = cv2.moments(cnt)
            if moments['m00']!=0:
                        cx = int(moments['m10']/moments['m00']) # cx = M10/M00
                        cy = int(moments['m01']/moments['m00']) # cy = M01/M00

            centr=(cx,cy)
            cv2.circle(img,centr,5,[0,0,255],2)
        ######################This line draws the center######################

            # Create bounding rectangle around the contour
            x,y,w,h = cv2.boundingRect(cnt)
            cv2.rectangle(crop_img,(x,y),(x+w,y+h),(0,0,255),0)

            # Find convex hull
            hull = cv2.convexHull(cnt)

            # Draw contour
            drawing = np.zeros(crop_img.shape,np.uint8)
            cv2.drawContours(drawing,[cnt],0,(0,255,0),0)
            cv2.drawContours(drawing,[hull],0,(0,0,255),0)

            # Find convexity defects
            hull = cv2.convexHull(cnt,returnPoints = False)
            defects = cv2.convexityDefects(cnt,hull)

            # Use cosine rule to find angle of the far point from the start and end point i.e. the convex points (the finger
            # tips) for all defects
            count_defects = 0

            for i in range(defects.shape[0]):
                s,e,f,d = defects[i,0]
                start = tuple(cnt[s][0])
                end = tuple(cnt[e][0])
                far = tuple(cnt[f][0])

                a = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
                b = math.sqrt((far[0] - start[0])**2 + (far[1] - start[1])**2)
                c = math.sqrt((end[0] - far[0])**2 + (end[1] - far[1])**2)
                angle = math.acos((b**2 + c**2 - a**2)/(2*b*c)) * 57

                #angle = (math.acos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c)) * 180) / 3.14

                if angle <= 90:
                    count_defects += 1
                    cv2.circle(crop_img,far,1,[0,0,255],-1)

                cv2.line(crop_img, start, end, [0, 0, 0], 2)
            # End for

            if count_defects == 1:
                str = "Two fingers up"
                cnt = 2
            elif count_defects == 2:
                str = "Three fingers up"
                cnt = 3
            elif count_defects == 3:
                str = "Four fingers up"
                cnt = 4
            elif count_defects == 4:
            	str= "\"Hi hi...\" "
            	cnt = 5
            else:
                str = "Recognizing Hand Gesture..."
                cnt = 0
            #cv2.putText(img, str, (30,100), cv2.FONT_HERSHEY_COMPLEX, 1.2, 1.2)

            self.publisher.publish(cnt)
            #self.rate.sleep()
            all_img = np.hstack((drawing, crop_img))
            cv2.imshow('Gesture and Contour Window', all_img)
            cv2.waitKey(3)

        except CvBridgeError, e:
            rospy.logerr(e)

if __name__ == '__main__':
    rospy.init_node(GestureRecognizer.NODE_NAME, anonymous=False)
    rospy.loginfo("Starting " + GestureRecognizer.NODE_NAME+"...")
    GestureRecognizer()
    try:
        rospy.loginfo(GestureRecognizer.NODE_NAME+" started succefully!")
        rospy.spin()
    except KeyboardInterrupt:
        rospy.loginfo("Stopping " + GestureRecognizer.NODE_NAME)
