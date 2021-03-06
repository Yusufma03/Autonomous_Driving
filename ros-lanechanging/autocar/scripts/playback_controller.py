#!/usr/bin/env python
import rospy 
from std_msgs.msg import Int32
from rosgraph_msgs.msg import Clock
from geometry_msgs.msg import Twist
from nav_msgs.msg import *
import numpy as np
import json
import os
import time

class PlaybackController:
    
    def __init__(self, cmds):
        self.cmds = cmds
        self.path2config = rospy.get_param('~path2config', None)
        with open(self.path2config, 'r') as f:
            self.config = json.load(f)
        self.pub = rospy.Publisher('robot_0/cmd_vel', Twist, queue_size=1)
        self.simu_running = False
        self.t_i = 0
        self.t_ros = 0
        self.end = False
        np.random.seed(self.config["random_seed"])
        
            
    def start_simu(self, msg):
        self.start_time = msg.data
        self.simu_running = True
    
    def send_control(self, cmd):
        msg = Twist()
        msg.linear.x = cmd[0]
        msg.linear.y = cmd[1]
        msg.angular.z = 0
        self.pub.publish(msg)
            
    def step(self, msg):
        if self.simu_running and msg.clock.secs >= self.start_time:

            self.t_ros += 1
            if self.t_ros == self.config["ros_dt_mult"]:
                self.t_ros = 0

                cmd = self.cmds[self.t_i]
                self.send_control(cmd)
                self.t_i += 1
                if self.t_i == len(self.cmds):
                    self.simu_running = False
                    self.end = True
                    self.send_control([0.0, 0.0])
        
    

if __name__=='__main__':
    
    rospy.init_node('playback_controller')
    path = rospy.get_param('~path2playback', None)

    with open(path,'r') as f:
        cmds = json.load(f)
            
        controller = PlaybackController(cmds)
        rospy.Subscriber('/start_simu', Int32, controller.start_simu, queue_size=1)
        rospy.Subscriber('/clock', Clock, controller.step, queue_size=1)

        while not controller.end and not rospy.is_shutdown():
            time.sleep(0.2)

