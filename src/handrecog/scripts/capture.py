#!/usr/bin/env python

import sys
import rospy
import cv2
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import numpy 



class image_converter:

	def __init__(self):
		self.bridge = CvBridge()
		self.image_pub = rospy.Publisher("/webcam_image",Image,queue_size=10)
		self.loop_rate = rospy.Rate(100)
	def start(self):
			cap = cv2.VideoCapture(0)
			if not cap.isOpened():
				print "Error opening resource: " + str(0)
				print "Maybe opencv VideoCapture can't open it"
				cap.open()
			rospy.loginfo("Timing images")
			#rospy.spin()
			rval,frame=cap.read();
			while not rospy.is_shutdown():
				    cv2.imshow("PUBLISHER",frame)
				    self.image_pub.publish(self.bridge.cv2_to_imgmsg(frame,"bgr8"))
				    rval,frame=cap.read();
				    self.loop_rate.sleep()


def main(args):
	  ic = image_converter()
	  try:
	    ic.start()
	  except KeyboardInterrupt:
	    print("Shutting down")
	  cv2.destroyAllWindows()

if __name__ == '__main__':
    rospy.init_node('image_converter', anonymous=True)
    main(sys.argv)


