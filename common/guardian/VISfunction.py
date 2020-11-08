from guardian import GuardState
from guardian import GuardStateDecorator
from guardian import NodeManager
import os
import sys
import kagralib as kgl

userapps = '/opt/rtcds/userapps/release/'
IFO = os.getenv('IFO')
ifo = IFO.lower()
SITE = os.getenv('SITE')
site = SITE.lower()
dorw = 2
verbose=False

def modelName(optic):
    return ifo+'vis'+optic

def req_file_path(optic):
    return os.path.join('/opt/rtcds',site,ifo,'target',modelName(optic),modelName(optic)+'epics')

def snap_file_path(optic):
#    return os.path.join(userapps, 'vis', ifo, 'burtfiles') 
    return os.path.join(userapps, 'vis', ifo, 'guardian') # FIXME temporary only

#reqfile = req_file_path(optic)
#snapfile = snap_file_path(optic)

#reqfile = req_file_path(optic)+'/autoBurt.req'
#snapfile = '/opt/rtcds/userapps/release/vis/k1/burtfiles/'+modelName(optic)+'_guardian_safe.snap'

###################################################


# utility functions

def is_tripped(optic,WD,BIO):
    # list of WD channel names and BIO channel names to be specified
    WD_state = False
    for name in WD:
        WD_state = WD_state or (ezca['VIS-'+optic+'_'+name+'_WDMON_STATE'] != 1) # check if any WD is tripped or not

    AnalogWD_state = False
    for name in BIO:
        AnalogWD_state = AnalogWD_state or ( (int(ezca['VIS-'+optic+'_BIO_'+name+'_MON']) & 983040) != 0 ) # check if any AnalogWD is tripped or not

    #check if DACKILL is tripped or not
    DACKILL_state = (ezca['VIS-'+optic+'_DACKILL_STATE'] != 1)

    if WD_state or AnalogWD_state or DACKILL_state:
        return True

    else:
        return False


# Temporary utility functions for SR testing only

def is_tripped2(optic,WD):
    # list of WD channel names and BIO channel names to be specified
    WD_state = False
    for name in WD:
        WD_state = WD_state or (ezca['VIS-'+optic+'_'+name+'_WDMON_STATE'] != 1) # check if any WD is tripped or not
        #    AnalogWD_state = False
        #    for name in BIO:
        #        AnalogWD_state = AnalogWD_state or ( (int(ezca['VIS-'+optic+'_BIO_'+name+'_MON']) & 983040) != #0 ) # check if any AnalogWD is tripped or not
        #        if WD_state or AnalogWD_state:
    if WD_state:
        return True
    else:
        return False


def is_pretripped(optic):
    if ezca['VIS-'+optic+'_IM_WD_OSEMAC_V1_RMSMON'] > 2000.0:
        return True
    elif ezca['VIS-'+optic+'_IM_WD_OSEMAC_V2_RMSMON'] > 2000.0:
        return True
    elif ezca['VIS-'+optic+'_IM_WD_OSEMAC_V3_RMSMON'] > 2000.0:
        return True
    elif ezca['VIS-'+optic+'_IM_WD_OSEMAC_H1_RMSMON'] > 2000.0:
        return True
    elif ezca['VIS-'+optic+'_IM_WD_OSEMAC_H2_RMSMON'] > 2000.0:
        return True
    elif ezca['VIS-'+optic+'_IM_WD_OSEMAC_H3_RMSMON'] > 2000.0:
        return True
    elif ezca['VIS-'+optic+'_BF_WD_AC_LVDT_V1_RMSMON'] > 100.0:
        return True
    elif ezca['VIS-'+optic+'_BF_WD_AC_LVDT_V2_RMSMON'] > 100.0:
        return True
    elif ezca['VIS-'+optic+'_BF_WD_AC_LVDT_V3_RMSMON'] > 100.0:
        return True
    elif ezca['VIS-'+optic+'_BF_WD_AC_LVDT_H1_RMSMON'] > 100.0:
        return True
    elif ezca['VIS-'+optic+'_BF_WD_AC_LVDT_H2_RMSMON'] > 100.0:
        return True
    elif ezca['VIS-'+optic+'_BF_WD_AC_LVDT_H3_RMSMON'] > 100.0:
        return True
    elif ezca['VIS-'+optic+'_SF_WD_AC_GAS_RMSMON'] > 100.0:
        return True
    else:
        return False


def tm_damp_off(optic):
    for DOF in ['L', 'P', 'Y']:
        ezca['VIS-'+optic+'_TM_DAMP_%s_TRAMP'%DOF] = 10.0
        ezca['VIS-'+optic+'_TM_DAMP_%s_GAIN'%DOF] = 0
    #time.sleep(10) # FIXME! no sleeping command.
    #for DOF in ['PIT','YAW']:
    #   ezca['VIS-'+optic+'_TM_OPLEV_SERVO_%s_TRAMP'%DOF] = 3.0
    #   ezca['VIS-'+optic+'_TM_OPLEV_SERVO_%s_GAIN'%DOF] = 0.0
        #ezca.switch('VIS-'+optic+'_TM_OPLEV_SERVO_%s'%DOF,'FM1','OFF')
    
def im_damp_off(optic):
    for DOF in ['L','T','V','R','P','Y']:
        ezca['VIS-'+optic+'_IM_DAMP_%s_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_IM_DAMP_%s_GAIN'%DOF] = 0

def im_offload_off(optic, TRAMP):
    for DOF in ['Y','P']:
        ezca['VIS-' + optic + '_IM_OL_DC_OFFLOAD_%s_TRAMP'%DOF] = TRAMP
        ezca['VIS-' + optic + '_IM_OL_DC_OFFLOAD_%s_GAIN'%DOF] = 0


def im_oldamp_off(optic):
    for DOF in ['P','Y']:
        ezca['VIS-'+optic+'_IM_OLDAMP_%s_TRAMP'%DOF] = 10.0
        ezca.switch('VIS-'+optic+'_IM_OLDAMP_%s'%DOF,'INPUT','OFF')
        #ezca['VIS-'+optic+'_IM_OLDAMP_%s_GAIN'%DOF] = 0
    

def bf_damp_off(optic):
    for DOF in ['L','T','V','R','P','Y']:
        ezca['VIS-'+optic+'_BF_DAMP_%s_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_BF_DAMP_Y_TRAMP'] = 10.0
        ezca['VIS-'+optic+'_BF_DAMP_%s_GAIN'%DOF] = 0

def gas_damp_off(optic):
    if (optic == 'PRM') or (optic == 'PR2') or (optic == 'PR3'):
    	for DOF in ['BF','SF']:
            ezca['VIS-'+optic+'_%s_DAMP_GAS_TRAMP'%DOF] = 10.0
            ezca.switch('VIS-'+optic+'_%s_DAMP_GAS'%DOF,'INPUT','OFF')
    elif (optic == 'BS') or (optic == 'SRM') or (optic == 'SR2') or (optic == 'SR3'):
        for DOF in ['BF','F0','F1']:
            ezca['VIS-'+optic+'_%s_DAMP_GAS_TRAMP'%DOF] = 10.0
            ezca['VIS-'+optic+'_%s_DAMP_GAS_GAIN'%DOF] = 0

def ip_damp_off(optic):
    for DOF in ['L','T','Y']:
        ezca['VIS-'+optic+'_IP_DAMP_%s_TRAMP'%DOF] = 10.0
        ezca['VIS-'+optic+'_IP_DAMP_%s_GAIN'%DOF] = 0


def test_off(optic):
    for DOF in ['L', 'P', 'Y']:
        ezca['VIS-'+optic+'_TM_TEST_%s_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_TM_TEST_%s_GAIN'%DOF] = 0
        ezca.switch('VIS-'+optic+'_TM_TEST_%s'%DOF,'OFFSET','OFF')
    for DOF in ['L','T','V','R','P','Y']:
        ezca['VIS-'+optic+'_IM_TEST_%s_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_IM_TEST_%s_GAIN'%DOF] = 0
        ezca.switch('VIS-'+optic+'_IM_TEST_%s'%DOF,'OFFSET','OFF')
    if (optic == 'PRM') or (optic == 'PR2') or (optic == 'PR3'):
        for DOF in ['L','T','V','R','P','Y']:
            ezca['VIS-'+optic+'_BF_TEST_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_BF_TEST_%s_GAIN'%DOF] = 0
            ezca.switch('VIS-'+optic+'_BF_TEST_%s'%DOF,'OFFSET','OFF')
        for DOF in ['BF','SF']:
            ezca['VIS-'+optic+'_%s_TEST_GAS_TRAMP'%DOF] = 10.0
            ezca['VIS-'+optic+'_%s_TEST_GAS_GAIN'%DOF] = 0
            ezca.switch('VIS-'+optic+'_%s_TEST_GAS'%DOF,'OFFSET','OFF')
    elif (optic == 'BS') or (optic == 'SRM') or (optic == 'SR2') or (optic == 'SR3'):
        for DOF in ['BF','F0','F1']:
            ezca['VIS-'+optic+'_%s_TEST_GAS_TRAMP'%DOF] = 10.0
            ezca['VIS-'+optic+'_%s_TEST_GAS_GAIN'%DOF] = 0

def opticalign_off(optic): # Added by A.Shoda. Please contact me if it is a problem.
    for DOF in ['P','Y']:
        ezca['VIS-'+optic+'_IM_OPTICALIGN_%s_TRAMP'%DOF] = 10.0
        ezca['VIS-'+optic+'_IM_OPTICALIGN_%s_GAIN'%DOF] = 0
        #ezca['VIS-'+optic+'_IM_OPTICALIGN_%s_GAIN'%DOF] = 0
            
def all_off(optic, self):
    if self.timer['waiting']:
        if self.counter == 1:
            tm_damp_off(optic)
            im_oldamp_off(optic)
            for DOF in ['P','Y']:
                ezca['VIS-'+optic+'_IM_OLDAMP_%s_TRAMP'%DOF] = self.TRAMP
                ezca['VIS-'+optic+'_IM_OLDAMP_%s_GAIN'%DOF] = 0

            test_off(optic)
            im_damp_off(optic)
            if (optic == 'PRM') or (optic == 'PR2') or (optic == 'PR3'):
                bf_damp_off(optic)
                im_offload_off(optic, self.TRAMP)
            elif (optic == 'BS') or (optic == 'SRM') or (optic == 'SR2') or (optic == 'SR3'):
                ip_damp_off(optic)
            elif (optic == 'ETMX') or (optic == 'ETMY') or (optic == 'ITMX') or (optic == 'ITMY'):
                bf_damp_off(optic)
                ip_damp_off(optic)
            gas_damp_off(optic)
            
            if (optic == 'PRM') or (optic == 'PR2') or (optic == 'PR3'):
                for DOF in ['BF','SF']:
                    ezca['VIS-'+optic+'_%s_DAMP_GAS_TRAMP'%DOF] = self.TRAMP
                    ezca['VIS-'+optic+'_%s_DAMP_GAS_GAIN'%DOF] = 0
                    ezca.switch('VIS-'+optic+'_%s_DAMP_GAS'%DOF,'OFFSET','OFF')
            opticalign_off(optic)
            self.timer['waiting'] = self.TRAMP
            self.counter += 1
        elif self.counter == 2:
            for DOF in ['BF','SF']:
                ezca['VIS-'+optic+'_%s_DAMP_GAS_RSET'%DOF] = 2
                ezca['VIS-'+optic+'_%s_DAMP_GAS_TRAMP'%DOF] = 0
                ezca['VIS-'+optic+'_%s_DAMP_GAS_GAIN'%DOF] = 1
                ezca['VIS-'+optic+'_%s_DAMP_GAS_TRAMP'%DOF] = self.TRAMP
            for DOF in ['P','Y']:
                ezca['VIS-'+optic+'_IM_OLDAMP_%s_RSET'%DOF] = 2
                ezca['VIS-'+optic+'_IM_OLDAMP_%s_TRAMP'%DOF] = 0
                ezca['VIS-'+optic+'_IM_OLDAMP_%s_GAIN'%DOF] = 1
                ezca['VIS-'+optic+'_IM_OLDAMP_%s_TRAMP'%DOF] = self.TRAMP
            self.counter += 1
        elif self.counter == 3:
            return True
    return False
        
    #time.sleep(10)

def get_dcuid(optic):
    # tower payload
    dcuids = {"ETMX": [102, 103],
              "ETMY": [107, 108],
              "ITMX": [92, 93],
              "ITMY": [97, 98],
              "BS":   [60, 61],
              "SR2":  [65, 66],
              "SR3":  [70, 71],
              "SRM":  [],
              "PR2":  [45],
              "PR3":  [50],
              "PRM":  []}
    return dcuids[optic]

def vis_watchdog_tripped(optic):
    '''
    Send alerts to people.
    '''
    #sendmail(sub=optic+' watchdog tripped!', text=optic+' watchdog has tripped. Please check the status.', to='yoichi.aso@nao.ac.jp')
    kgl.speak_aloud(optic+' watchdog has tripped')
    kgl.speak_aloud(optic+' watchdog has tripped')
    kgl.speak_aloud('Please check the status of '+optic)        

def vis_pay_watchdog_tripped(optic):
    '''
    Send alerts to people.
    '''
    #sendmail(sub=optic+' watchdog tripped!', text=optic+' watchdog has tripped. Please check the status.', to='yoichi.aso@nao.ac.jp')
    kgl.speak_aloud(optic+' payload watchdog has tripped')
    kgl.speak_aloud(optic+' payload watchdog has tripped')
    kgl.speak_aloud('Please check the status of '+optic)        

