####
## Control system for watch dog
## Coded by A. Shoda 15/08/25
####


import commands as cmd
import os
import time

ChkFilt = ['F0', 'IM', 'TM', 'GAS','TM_OPLEV','IM_OPLEV','TM_GLOBALF']
DOFdict = {'TM':['L','P','Y'], 'IM':['L','T','V','P','Y','R'], 'F0':['L','T','Y'], 'GAS':['F0','F1','F2'],'TM_OPLEV':['P','Y'],'IM_OPLEV':['P','Y'],'TM_GLOBALF':['L']}

def CheckStatus(switch=True):
  Status = [0,0,0,0,0]
  
  num_blend = 0
  for dof in DOFdict['F0']:
    FiltName0 = 'K1:VIS-PROTO_F0_BLEND_BLEND'+dof+'0_GAIN'
    gain = cmd.getoutput('tdsread '+FiltName0)
    if int(gain) == 1:
      num_blend += 1
  if num_blend == len(DOFdict['F0']):
    Status[0] = 1
  
  num_lvdt = 0
  for dof in DOFdict['F0']:
    FiltName = 'K1:VIS-PROTO_F0_BLEND_BLEND'+dof+'_GAIN'
    gain = cmd.getoutput('tdsread '+FiltName)
    if int(gain) == 1:
      num_lvdt += 1
  if num_lvdt == len(DOFdict['F0']):
    Status[0] = 2
  
  for dof in DOFdict['F0']:
    FiltName = 'K1:VIS-PROTO_F0_SERVOF_'+dof+'_GAIN'
    gain = cmd.getoutput('tdsread '+FiltName)
    if int(gain) == 0:
      Status[0] = 0
      break
    
  num_gas = 0
  for dof in DOFdict['GAS']:
    FiltName = 'K1:VIS-PROTO_GAS_SERVOF_'+dof+'_GAIN'
    gain = cmd.getoutput('tdsread '+FiltName)
    if int(gain) == -1:
      num_gas += 1
  if num_gas == len(DOFdict['GAS']):
    Status[1] = 1
   
  num_oplev = 0
  Status[3]=1
  for dof in DOFdict['IM_OPLEV']:
    FiltName = 'K1:VIS-PROTO_IM_OPLEVF_'+dof+'_GAIN'
    gain = cmd.getoutput('tdsread '+FiltName)
    if int(gain) == 0:
      Status[3]=0
      break
  
  if Status[3] == 0: 
    num_osem = 0
    for dof in DOFdict['TM']:
      FiltName = 'K1:VIS-PROTO_TM_SERVOF_'+dof+'_GAIN'
      gain = cmd.getoutput('tdsread '+FiltName)
      if int(gain) == -1:
        num_osem += 1
  
    for dof in DOFdict['IM']:
      FiltName = 'K1:VIS-PROTO_IM_SERVOF_'+dof+'_GAIN'
      gain = cmd.getoutput('tdsread '+FiltName)
      if int(gain) == -1:
        num_osem += 1
        
    if num_osem == len(DOFdict['TM'])+len(DOFdict['IM']):
      Status[2] = 1

  if Status[3] == 1: 
    num_osem = 0
    for dof in ['L']:
      FiltName = 'K1:VIS-PROTO_TM_SERVOF_'+dof+'_GAIN'
      gain = cmd.getoutput('tdsread '+FiltName)
      if int(gain) == -1:
        num_osem += 1
  
    for dof in ['L','T','V','R']:
      FiltName = 'K1:VIS-PROTO_IM_SERVOF_'+dof+'_GAIN'
      gain = cmd.getoutput('tdsread '+FiltName)
      if int(gain) == -1:
        num_osem += 1
        
    if num_osem == len(DOFdict['TM'])-2+len(DOFdict['IM'])-2:
      Status[2] = 1

  FiltName = 'K1:VIS-PROTO_TM_GLOBALF_L_GAIN'
  gain = cmd.getoutput('tdsread '+FiltName)
  if int(gain) == -1:
    Status[4] = 1

  return Status


def CheckStatus_md(Status):
  blend = cmd.getoutput('tdsread K1:VIS-PROTO_STATUS_SERVO_Blend')
  blend0 = cmd.getoutput('tdsread K1:VIS-PROTO_STATUS_SERVO_Blend0')
  GAS = cmd.getoutput('tdsread K1:VIS-PROTO_STATUS_SERVO_GAS')
  OSEM = cmd.getoutput('tdsread K1:VIS-PROTO_STATUS_SERVO_OSEM')
  OL = cmd.getoutput('tdsread K1:VIS-PROTO_STATUS_SERVO_OL')
  PS = cmd.getoutput('tdsread K1:VIS-PROTO_STATUS_SERVO_PS')
  
  Status = [int(blend0),int(GAS),int(OSEM), int(OL), int(PS)]
  if blend == '1':
    Status[0] = 2
  
  return Status

def SwitchStatusSwitch(Status, switch=True):
  if switch==True:
    #prnt 'Switch'
    if Status == [2,1,0,1,1]:	#Observation State
      #print 'Observation'
      a = cmd.getoutput('tdswrite K1:VIS-PROTO_STATE1 0')
      a = cmd.getoutput('tdswrite K1:VIS-PROTO_STATE2 0')
      a = cmd.getoutput('tdswrite K1:VIS-PROTO_STATE3 1')
      #a = cmd.getoutput('tdswrite K1:VIS-PROTO_STATE4 0')
    
    elif Status == [2,1,1,1,0]:	#Lock Acquisition State
      #print 'Lock Acq'
      a = cmd.getoutput('tdswrite K1:VIS-PROTO_STATE1 0')
      a = cmd.getoutput('tdswrite K1:VIS-PROTO_STATE2 1')
      a = cmd.getoutput('tdswrite K1:VIS-PROTO_STATE3 0')
      #a = cmd.getoutput('tdswrite K1:VIS-PROTO_STATE4 0')
    
    elif Status == [1,1,1,0,0] or Status ==[2,1,1,0,0]:
      #print 'Damping mode'	#Damping State
      a = cmd.getoutput('tdswrite K1:VIS-PROTO_STATE1 1')
      a = cmd.getoutput('tdswrite K1:VIS-PROTO_STATE2 0')
      a = cmd.getoutput('tdswrite K1:VIS-PROTO_STATE3 0')
      #a = cmd.getoutput('tdswrite K1:VIS-PROTO_STATE4 0')
    
    elif Status == [0,0,0,0,0]:
      #print 'Emergency'
      a = cmd.getoutput('tdswrite K1:VIS-PROTO_STATE1 0')
      a = cmd.getoutput('tdswrite K1:VIS-PROTO_STATE2 0')
      a = cmd.getoutput('tdswrite K1:VIS-PROTO_STATE3 0')
      a = cmd.getoutput('tdswrite K1:VIS-PROTO_STATE4 1')
    
    else:
      #print 'Nothing'
      a = cmd.getoutput('tdswrite K1:VIS-PROTO_STATE1 0')
      a = cmd.getoutput('tdswrite K1:VIS-PROTO_STATE2 0')
      a = cmd.getoutput('tdswrite K1:VIS-PROTO_STATE3 0')
      #a = cmd.getoutput('tdswrite K1:VIS-PROTO_STATE4 0')
  

def Off(Status):
  Write = cmd.getoutput('/users/sekiguchi/apps/k1visproto_ctrl_off_2.sh')
  Status = [0,0,0,0,0]
  SwitchStatusSwitch(Status)
  return Status

def Dmp(Status):
  ## Turn on OSEMs
  Write = cmd.getoutput('/users/sekiguchi/apps/osem_ctrl_on.sh')
  Status[2] = 1
  ## Turn off PS
  Write = cmd.getoutput('/users/sekiguchi/apps/global_ctrl_off.sh')
  #Write = cmd.getoutput('tdswrite K1:VIS-PROTO_TM_GLOBALF_L_TRAMP 5.0')
  #Write = cmd.getoutput('tdswrite K1:VIS-PROTO_TM_GLOBALF_L_GAIN 0.0')
  Status[4] = 0
  ## Turn off Oplev
  Write = cmd.getoutput('/users/sekiguchi/apps/oplev_ctrl_off.sh')
  Status[3] = 0
  ## Turn off Blending
  Write = cmd.getoutput('/users/sekiguchi/apps/blend_off.sh')
  Status[0] = 1
  SwitchStatusSwitch(Status)
  
  return Status



def DmpToBlending(Status):
  ## Turn on Blending
  Write = cmd.getoutput('/users/sekiguchi/apps/blend_on.sh')
  Status[0] = 2
  SwitchStatusSwitch(Status)
  
  return Status

def BlendToLock(Status):
  ## Turn on Oplev
  Write = cmd.getoutput('/users/sekiguchi/apps/oplev_ctrl_on.sh')
  Status[3] = 1
  SwitchStatusSwitch(Status)
  
  return Status
  
def LockToObs(Status):
  ##Turn on PS
  #Write = cmd.getoutput('tdswrite K1:VIS-PROTO_TM_GLOBALF_L_TRAMP 5.0')
  #Write = cmd.getoutput('tdswrite K1:VIS-PROTO_TM_GLOBALF_L_RSET 2')
  #Write = cmd.getoutput('tdswrite K1:VIS-PROTO_TM_GLOBALF_L_GAIN -1.0')
  Write = cmd.getoutput('/users/sekiguchi/apps/global_ctrl_on.sh')
  Status[4] = 1
  Write = cmd.getoutput('/users/sekiguchi/apps/osem_ctrl_off.sh')
  Status[2] = 0
  SwitchStatusSwitch(Status)
  
  return Status
