from guardian import GuardState
import time
from VIS_DICT import *
##################################################
# initialization values

# initial REQUEST state
request = 'MON_ALL'

# NOMINAL state, which determines when node is OK
nominal = 'MON_ALL'
IFO = 'K1'
subsystem = 'VIS'
prefix = 'VIS'
##################################################
##################################################
def check():
    
    for _type in VIS_DICT['type']: # _type: typeA, typeB....
#        log(_type)
        
        for OPTIC in VIS_DICT[_type]: # OPTIC: ITMX, ITMY....
            notify('Checking '+OPTIC+' input channels')
            bad_list=[]
            warning_list=[]
            for INMON in VIS_DICT[_type+'_INMON']: # INMON IP_LVDTINF_H1, IPLVDTINF_H2...
#                log(ezca['VIS-SRM_IP_LVDTINF_H1_INMON'])
                if 'SUM' in INMON:
                    lower_lim=VIS_DICT[OPTIC+'_INMON_lim'][INMON][0]
                    val=ezca[OPTIC+'_'+INMON+'_INMON']
                    if val<=lower_lim:
                        bad_list+=[prefix+'-'+OPTIC+'_'+INMON+'_INMON']
                else:
                    lower_lim=VIS_DICT[OPTIC+'_INMON_lim'][INMON][0]
                    upper_lim=VIS_DICT[OPTIC+'_INMON_lim'][INMON][1]
                    val_range=(upper_lim-lower_lim)/2
                    val_offset=(upper_lim+lower_lim)/2
                    val=ezca[OPTIC+'_'+INMON+'_INMON']-val_offset
                    if abs(val)>=val_range*0.9:
                        bad_list+=[prefix+'-'+OPTIC+'_'+INMON+'_INMON']
                    elif abs(val)>=val_range*0.5:
                        warning_list+=[prefix+'-'+OPTIC+'_'+INMON+'_INMON']
#            print(bad_list)
#            log('['+OPTIC+'] %d sensor channel(s) used up at least 90%% of range'%(len(bad_list)))
#            log('['+OPTIC+'] %d sensor channel(s) used up at least 50%% of range'%(len(warning_list)))      
            for level in VIS_DICT[_type+'_levels']: # level: IP, F0, F1.....
                if any([level in chan.rstrip('INMON') for chan in bad_list]): # Here we use rstrip because ('TM' in '*OUTMON' is true...) should probably changed to '_'+level+'_' instead but will see how it goes.
                    ezca[OPTIC+'_'+level+'_INMON']=3
                elif any([level in chan.rstrip('INMON') for chan in warning_list]):
                    ezca[OPTIC+'_'+level+'_INMON']=2
                else:
                    ezca[OPTIC+'_'+level+'_INMON']=1
            ####################################################################################            
            notify('Checking '+OPTIC+' output channels')
            bad_list=[]
            warning_list=[]
            healthy_list=[]
            for OUTMON in VIS_DICT[_type+'_OUTMON']: # OUTMON IP_COILOUTF_H1, IP_COILOUTF_H2...
#                log(ezca['VIS-SRM_IP_LVDTINF_H1_OUTMON'])
                if 'SUM' in OUTMON:
                    lower_lim=VIS_DICT[OPTIC+'_OUTMON_lim'][OUTMON][0]
                    val=ezca[OPTIC+'_'+OUTMON+'_OUTMON']
                    if val<=lower_lim:
                        bad_list+=[prefix+'-'+OPTIC+'_'+OUTMON+'_OUTMON']
                else:
                    lower_lim=VIS_DICT[OPTIC+'_OUTMON_lim'][OUTMON][0]
                    upper_lim=VIS_DICT[OPTIC+'_OUTMON_lim'][OUTMON][1]
                    val_range=(upper_lim-lower_lim)/2
                    val_offset=(upper_lim+lower_lim)/2
                    val=ezca[OPTIC+'_'+OUTMON+'_OUTPUT']
                    if abs(val)>=val_range*0.9:
                        bad_list+=[prefix+'-'+OPTIC+'_'+OUTMON+'_OUTMON']
                    elif abs(val)>=val_range*0.5:
                        warning_list+=[prefix+'-'+OPTIC+'_'+OUTMON+'_OUTMON']
                    elif abs(val)>=val_range*10**-6:
                        healthy_list+=[prefix+'-'+OPTIC+'_'+OUTMON+'_OUTMON']
#                    if 'TM' in OUTMON:
#                        log('TM:%.2f'%abs(val)+OUTMON)
#            print(healthy_list)
#            log('['+OPTIC+'] %d actuator channel(s) used up at least 90%% of range'%(len(bad_list)))
#            log('['+OPTIC+'] %d actuator channel(s) used up at least 50%% of range'%(len(warning_list)))
            #if OPTIC=='BS':
            #    log(warning_list) 
            for level in VIS_DICT[_type+'_levels']: # level: IP, F0, F1.....
                if any([level in chan.rstrip('OUTMON') for chan in bad_list]):
                    ezca[OPTIC+'_'+level+'_OUTMON']=3
                elif any([level in chan.rstrip('OUTMON') for chan in warning_list]):
                    ezca[OPTIC+'_'+level+'_OUTMON']=2
                elif any([level+'_' in chan.rstrip('OUTMON') for chan in healthy_list]):
                    ezca[OPTIC+'_'+level+'_OUTMON']=1
                else:
                    ezca[OPTIC+'_'+level+'_OUTMON']=0
            ######################################################################
            WD_BAD=0
            for level in VIS_DICT[_type+'_levels']: # level: IP, F0, F1......
                if ezca[OPTIC+'_'+level+'_WDMON_STATE']==2:
                    WD_BAD=1
                    break
            ezca[OPTIC+'_WD']=WD_BAD
#            log('%s [%d,%d]'%(INMON,VIS_DICT[OPTIC+'_INMON_lim'][INMON][0],VIS_DICT[OPTIC+'_INMON_lim'][INMON][1]))
                
#    H1=ezca['VIS-ITMX_IP_LVDTINF_H1']
#    notify('%.2f'%(H1))
##################################################
class INIT(GuardState):
    index=0
    request=False
    def main(self):
		return(True)

class IDLE(GuardState):
    index=1
    request=True
    goto=True
    def main(self):
		return(True)

class MON_INPUT_ONLY(GuardState):
    index=2
    def run(self):
        return(True)

class MON_OUTPUT_ONLY(GuardState):
    index=3
    def run(self):
        return(True)

class MON_ALL(GuardState):
    index=4
    def run(self):
        check()
        return(True)

edges=[
('INIT','IDLE'),
('IDLE','MON_INPUT_ONLY'),
('IDLE','MON_OUTPUT_ONLY'),
('IDLE','MON_ALL')
]
