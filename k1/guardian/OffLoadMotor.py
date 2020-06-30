# -*- coding: utf-8 -*-
"""
Created on Wed Nov 22 20:01:32 2017

@author: Ayaka

This code is for offload the offset of the coil driver output by motors in the guardian script
"""
import sys
sys.path.append('/kagra/Dropbox/Subsystem/TypeBp/Scripts/steppingmotor/')
from Trinamic_control6110 import *


### for picomotor ###
def move_pico(motorPV, sign, **kwarg): 
    # motorPV: the process valuable for pico
    # sign: the direction to move the motors. if step in +, chose 1. otherwise, chose 0.
    # step(optional): step number to move
    
    if kwarg  
    return

### for stepping motors ###
def move_GASstep(optic, stage, sign, m_driver, m_number, **kwarg):
    # sign: the direction to move the motors. if step in +, chose 1, otherwise, chose 0.
    # m_driver: motor driver ip address
    # m_number: motor number
    # step(optional): step number to move
    
    if kwarg
          
    return

def move_IPstep(sign, )
