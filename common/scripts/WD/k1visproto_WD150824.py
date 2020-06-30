#!/bin/sh python

####
## Control system for watch dog
## Coded by A. Shoda 15/08/25
####

import commands as cmd
import os
import time
import k1visproto_Ctrl as ctrl
import SendAlert

#Define the filters and DOF to control
ChkFilt = ['F0', 'IM', 'TM', 'GAS']
DOFdict = {'TM':['L','P','Y'], 'IM':['L','T','V','P','Y','R'], 'F0':['L','T','Y'], 'GAS':['F0','F1','F2'],'TM_OPLEV':['P','Y'],'IM_OPLEV':['P','Y'],'TM_GLOBALF':['L']}


def CheckandDmp(Status, status_clock):	#check status and if error occurs, go to damping mode
    if Status == [0,0,0,0,0]:
      return Status

    else:
      for filt in ChkFilt:
        for dof in DOFdict[filt]:
          FiltName = 'K1:VIS-PROTO_'+filt+'_WD_out_FLAG_'+dof
          flag = cmd.getoutput('tdsread '+FiltName)
        
          # If something wrong (flag=0) -> Switch to the Damping mode
          if flag == '0':
  	    ## check if the status is still bad after 1 sec
	    time.sleep(1)
	    flag2 = cmd.getoutput('tdsread '+FiltName)
	
	    if flag2 =='0':
	      ## Switch to the Damping mode
             Status = ctrl.Dmp(Status)
             SendAlert.Dmp()
             Status = CheckOutput(Status)	# Wait until all the outputs become OK after turn into the damping mode
             status_clock = time.time()	# Initialize status clock
             return Status, status_clock
	  
      if Status[0] == 2:
        for dof in range(3):
          FiltName = 'K1:VIS-PROTO_F0_WD_seis_FLAG_H'+str(dof+1)
          flag = cmd.getoutput('tdsread '+FiltName)
          # If something wrong (flag=0) -> Switch to the Damping mode
          if flag == '0':
	    ## Switch to the Damping mode
	    Status = ctrl.Dmp(Status)
	    SendAlert.Dmp()
	    Status = CheckOutput(Status)
	    status_clock = time.time()
	    return Status, status_clock

      if Status[3] == 1:
        flag_s = cmd.getoutput('tdsread K1:VIS-PROTO_OL_WD_RMSOUT_SUMFlag1')
        # If something wrong (flag=0) -> Switch to the Damping mode
        if flag_s != '1':
	  ## Switch to the Damping mode
	  Status = ctrl.Dmp(Status)
	  SendAlert.Dmp()
	  Status = CheckOutput(Status)
	  status_clock = time.time()
	  return Status, status_clock
	  
      return Status, status_clock


def CheckandDmp_md(Status):
  if Status == [0,0,0,0,0]:
    return Status
  
  else:
    flag_out = cmd.getoutput('tdsread K1:VIS-PROTO_STATE_FLAG_OUTPUT')
    
    

def CheckandOff(Status):	#check status and if error occurs, go to damping mode
    for filt in ChkFilt:
      for dof in DOFdict[filt]:
        FiltName = 'K1:VIS-PROTO_'+filt+'_WD_out_FLAG_'+dof
        flag = cmd.getoutput('tdsread '+FiltName)
        
        # If something wrong (flag=0) -> Switch to the Damping mode
        if flag == '0':
	  ## check if the status is still bad after 1 sec
	  time.sleep(1)
	  flag2 = cmd.getoutput('tdsread '+FiltName)
	
	  if flag2 =='0':
	    ## Switch to the Damping mode
	    Status = ctrl.Off(Status)
	    SendAlert.Dmp()
	    return Status
	  
    if Status[0] == 2:
      for dof in range(3):
        FiltName = 'K1:VIS-PROTO_F0_WD_seis_FLAG_H'+str(dof+1)
        flag = cmd.getoutput('tdsread '+FiltName)
        # If something wrong (flag=0) -> Switch to the Damping mode
        if flag == '0':
	  ## Switch to the Damping mode
	  Status = ctrl.Off(Status)
	  SendAlert.Dmp()
	  return Status
	  
    return Status  
 

def CheckOutput(Status):	#check the output flag status after get into the damping mode. 
    ## if the all output become ok, get out of the function. if the any of the outputs is wrong, stay in the function. 
    ## When the calculation time gets larger than 600sec, turn off all the control and get out of the function.
    time0 = time.time()	#time to get into the damping mode
    flag_All = 0
    timenow = time.time()
    while timenow - time0 < 600. and flag_All == 0:
      num = 0	#Initialize the count
      for filt in ChkFilt:
        for dof in DOFdict[filt]:
          FiltName = 'K1:VIS-PROTO_'+filt+'_WD_out_FLAG_'+dof
          flag = cmd.getoutput('tdsread '+FiltName)	#Read output flags
           
          ## If something wrong (flag=0) -> Count
          if flag == '0':
            num = 1	#Count
            break
       
      if num == 0: #If not counted
        flag_All = 1	# flag OK
      
      time.sleep(5)	#Wait 5 sec
      timenow = time.time()	#time now

    if timenow - time0 >= 600. and flag_All == 0:	# If flags are 0 for 600 sec, then turn into the emergency mode.
      Status = ctrl.Off(Status)
      ctrl.SwitchStatusSwitch(Status)
      SendAlert.Emergency()
      return Status
    
    else:	# If the flags are 1, break the roop
      return Status

status_clock = time.time()	# time when the status changes

while True:

    if cmd.getoutput('tdsread K1:VIS-PROTO_STATE4') == '1':
      continue

    #Status = ctrl.CheckStatus(switch=True)
    Status = ctrl.CheckStatus(switch=True)
    Status, status_clock = CheckandDmp(Status, status_clock)	## In any status, check the WD flags and if flag turns to red, go to damping mode

    print Status, status_clock

    if cmd.getoutput('tdsread K1:VIS-PROTO_STATE4') == '1':
      continue

    #if Status == [2,1,1,1,1]:	## Observation Mode
    
    if Status == [2,1,1,1,0] and time.time() - status_clock > 60.:	## 1min from Lock acquisition mode 
      Status = ctrl.LockToObs(Status)
      SendAlert.LockToObs()
      status_clock = time.time()

    if Status[0] == 1:	## Can I get Blending On?
      num = 0
      ## if OK, turn on blending
      for dof in range(3):	#Check Geophone signal
	 FiltName = 'K1:VIS-PROTO_F0_WD_seis_FLAG_H'+str(dof+1)
	 flag = cmd.getoutput('tdsread '+FiltName)
	 if flag == '0':
	   num = 1
	   break
      for dof in DOFdict['F0']:	#Check Blending signal
	 FiltName = 'K1:VIS-PROTO_F0_BLEND_WD_FLAG_'+dof
	 flag = cmd.getoutput('tdsread '+FiltName)
	 if flag == '0':
	   num = 1
	   break
      if num == 0:
	 Status = ctrl.DmpToBlending(Status)
	 status_clock = time.time()
      
    if Status == [2,1,1,0,0] or Status == [1,1,1,0,0]:	## can I get Oplev On?
      #Turn on Oplev if OK
      timenow = time.time()
      flag_s = cmd.getoutput('tdsread K1:VIS-PROTO_OL_WD_RMSOUT_SUMFlag1')
      flag_h = cmd.getoutput('tdsread K1:VIS-PROTO_OL_WD_FLAG_HOR1')
      flag_v = cmd.getoutput('tdsread K1:VIS-PROTO_OL_WD_FLAG_VER1')
      flag_mail = cmd.getoutput('tdsread K1:VIS-PROTO_STATE5')
      if flag_s == '1' and flag_h == '0' and flag_v == '0':	# Oplev signal is on the QPD
	 Status = ctrl.BlendToLock(Status)
	 status_clock = time.time()
      elif timenow - status_clock > 600. and flag_mail=='0':	# If not, at 10 min after the status changes
	 SendAlert.Oplev()
	 flag = cmd.getoutput('tdswrite K1:VIS-PROTO_STATE5 1')
	
	
