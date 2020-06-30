#!/bin/sh python

#Python watchdog script for TAMA experiment.
#Written by A. Shoda. 2015/08/17

import commands as cmd
import os
import time
import k1visproto_Ctrl as ctrl
import SendAlert

#Define the filters and DOF to control
ChkFilt = ['F0', 'IM', 'TM', 'GAS','TM_OPLEV','IM_OPLEV','TM_GLOBALF']
DOFdict = {'TM':['L','P','Y'], 'IM':['L','T','V','P','Y','R'], 'F0':['L','T','Y'], 'GAS':['F0','F1','F2'],'TM_OPLEV':['P','Y'],'IM_OPLEV':['P','Y'],'TM_GLOBALF':['L']}


def CheckandDmp(Status):	#check status and if error occurs, go to damping mode
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
	    return Status
	  
    if Status[0] == 2:
      for dof in DOFdict['F0']:
        FiltName = 'K1:VIS-PROTO_F0_WD_seis_FLAG_'+dof
        flag = cmd.getoutput('tdsread '+FiltName)
        # If something wrong (flag=0) -> Switch to the Damping mode
        if flag == '0':
	  ## Switch to the Damping mode
	  Status = ctrl.Dmp(Status)
	  SendAlert.Dmp()
	  return Status
	  
    return Status

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
        FiltName = 'K1:VIS-PROTO_F0_WD_seis_FLAG_H'+str(dof)
        flag = cmd.getoutput('tdsread '+FiltName)
        # If something wrong (flag=0) -> Switch to the Damping mode
        if flag == '0':
	  ## Switch to the Damping mode
	  Status = ctrl.Off(Status)
	  SendAlert.Dmp()
	  return Status
	  
    return Status  
 

def Check():	#check the flag status
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
	    return Status
	  
    if Status[0] == 2:
      for dof in DOFdict['F0']:
        FiltName = 'K1:VIS-PROTO_F0_WD_seis_FLAG_'+dof
        flag = cmd.getoutput('tdsread '+FiltName)
        # If something wrong (flag=0) -> Switch to the Damping mode
        if flag == '0':
	  ## Switch to the Damping mode
	  Status = ctrl.Dmp(Status)
	  SendAlert.Dmp()
	  return Status
	  
    return Status

while True:
    #Status = ctrl.CheckStatus(switch=True)
    Status = ctrl.CheckStatus(switch=False)
    Status = CheckandOff(Status)	## In any status, check the WD flags and if flag turns to red, go to damping mode
    
	
	  
	

      
