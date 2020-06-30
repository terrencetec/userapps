#===================================================
# TYPEA gardian
#
# created on Aug 1 2019 based on VIS_ETMY.py by KK
#===================================================

import time
import math
from guardian import GuardState
from guardian import GuardStateDecorator
from guardian import NodeManager
import os
import sys
import subprocess
import VISfunction as vf
import typea_lib as lib
import typeaparams as par

# importing a set of useful functions.
sys.path.append('/opt/rtcds/userapps/release/vis/common/guardian/')


__,optic = SYSTEM.split('_')

##################################################
# initial REQUEST state
request = 'INIT'

# NOMINAL state, which determines when node is OK
nominal = 'ALIGNED'

reqfile = vf.req_file_path(optic)+'/autoBurt.req'
snapfile = '/opt/rtcds/userapps/release/vis/k1/burtfiles/'+vf.modelName(optic)+'_guardian_safe.snap'


##################################################
# STATE decorators

class watchdog_check(GuardStateDecorator):
    """Decorator to check watchdog"""
    def pre_exec(self):
        if lib.is_twr_tripped(optic, par.BIO_TWR):
            log("All tripped.")
            return 'TRIPPED'
        elif lib.is_pay_tripped(optic,par.BIO_PAY):
            log("Payload is tripped")
            return 'PAY_TRIPPED'

class oplev_check(GuardStateDecorator):
    """Decorator to check oplev"""
    def pre_exc(self):
        if not lib.is_oplev_inrange(optic):
            log('Some optical lever is out of range')
            return 'OPLEV_OUTOFRANGE'

# ------- Made by T. Ushiba 2019/8/20 -------#
#class oplev_RMS_check(GuardStateDecorator):
#    """Decorator to check oplev RMS"""
#    def pre_exec(self):
#        if lib.is_oplev_noisy(optic):
#            log('OpLev RMS is too large to engage OpLev damp')
#            return 'CALM_DOWN'
#        else:
#            log('ALIGNED')
#            return 'ALIGNED'
#--------------------------------------------#

        
##################################################
class INIT(GuardState):
    index = 0
    goto = False
    

class TRIPPED(GuardState):
    index = 1
    redirect = False
    request = False
    def main(self):
        notify("please restart WatchDog!")
        vf.vis_watchdog_tripped(optic)

    def run(self):
        lib.all_off_quick(self,optic)
        for DOF in ['P','Y']:
            ezca['VIS-'+optic+'_MN_TMOLDAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_MN_TMOLDAMP_%s_GAIN'%DOF] = 1
        ezca['VIS-'+optic+'_PAY_MASTERSWITCH'] = 'OFF'
        ezca['VIS-'+optic+'_MASTERSWITCH'] = 'OFF'

        
        return not (lib.is_pay_tripped(optic,par.BIO_PAY) or lib.is_twr_tripped(optic,par.BIO_TWR))


class PAY_TRIPPED(GuardState):
    index = 2
    redirect = False
    request = False
    def main(self):
        lib.pay_off(self, optic, oaOffFlag=False)
        notify("please restart WatchDog!")
        vf.vis_pay_watchdog_tripped(optic)

    def run(self):
        for DOF in ['P','Y']:
            ezca['VIS-'+optic+'_MN_TMOLDAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_MN_TMOLDAMP_%s_GAIN'%DOF] = 1

            ezca.get_LIGOFilter('VIS-'+optic+'_MN_MNOLDAMP_%s'%DOF).turn_off('INPUT')
            ezca['VIS-'+optic+'_MN_MNOLDAMP_%s_RSET'%DOF] = 2
        if not lib.is_pay_tripped(optic,['MNH','MNIMV','IMH','TM']):

            return True

#class OPLEV_OUTOFRANGE(GuardState):
#    index = 3
#    redirect = False
#    request = False
#    @watchdog_check
#    def main(self):
#        log('Oplev is out of range. Turning off the oplev controls')
#        lib.tm_damp_off(self,optic)
#        lib.im_oldamp_off(self,optic)
#        lib.mn_oldamp_off(self,optic)
#        lib.bf_oldamp_off(self,optic)
#            
#        lib.mn_mnoldamp_off(self,optic)
#        return True
#    def run(self):
#        if lib.is_oplev_inrange(optic):
#            return True

        
class RESET(GuardState):
    index = 21
    goto = False
    request = False
    def main(self):
        #log('Turning off the master switch')
        #lib.all_off(self,optic)
        #ezca['VIS-'+optic+'_MASTERSWITCH'] = 'OFF'
        return True

class SAFE(GuardState):
    """Safe state is with master switch off not to send any signal"""
    index = 30
    @watchdog_check
    def main(self):
        log('Start to turn all damping off')
        lib.all_off(self,optic)
        MNP = ezca.get_LIGOFilter('VIS-'+optic+'_MN_TMOLDAMP_P')
        MNY = ezca.get_LIGOFilter('VIS-'+optic+'_MN_TMOLDAMP_Y')
        MNP.ramp_gain(0,0,False)
        MNY.ramp_gain(0,0,False)
        MNP.turn_off('INPUT')
        MNY.turn_off('INPUT')
        MNP.RSET.put(2)
        MNY.RSET.put(2)
        
        log('Turning off the master switch')
        ezca['VIS-'+optic+'_PAY_MASTERSWITCH'] = 'OFF'
        ezca['VIS-'+optic+'_MASTERSWITCH'] = 'OFF'
        subprocess.call(['burtrb', '-f', reqfile, '-o', snapfile, '-l','/tmp/controls.read.log', '-v'])

    @watchdog_check
    def run(self):
        return True

    
class OUTPUT_ON(GuardState):
    index = 41
    request = False

    @watchdog_check
    def main(self):
        log('Turning on the master switch')
        ezca['VIS-'+optic+'_MASTERSWITCH'] = 'ON'
        ezca['VIS-'+optic+'_PAY_MASTERSWITCH'] = 'ON'
	log('Turning on the TEST filters')
	## IP ##
        for DOF in ['L','T','Y']:
            ezca['VIS-'+optic+'_IP_TEST_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_IP_TEST_%s_GAIN'%DOF] = 1.0
        ezca['VIS-'+optic+'_IP_DAMPMODE_LOAD_MATRIX'] = 1.0
	## GAS ##
        for DOF in ['BF','F3','F2','F1','F0']:
            ezca['VIS-'+optic+'_%s_TEST_GAS_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_%s_TEST_GAS_GAIN'%DOF] = 1.0
	## BF, MN and IM ##
        for DOF in ['L','T','V','R','P','Y']:
            ezca['VIS-'+optic+'_BF_TEST_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_BF_TEST_%s_GAIN'%DOF] = 1.0

            ezca['VIS-'+optic+'_MN_TEST_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_MN_TEST_%s_GAIN'%DOF] = 1.0

            ezca['VIS-'+optic+'_IM_TEST_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_IM_TEST_%s_GAIN'%DOF] = 1.0
        ## TM ##
        for DOF in ['L','P','Y']:
            ezca['VIS-'+optic+'_TM_TEST_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_TM_TEST_%s_GAIN'%DOF] = 1.0
        lib.wait(self,5)

        ## Optic Align
        for DOF in ['P','Y']:
            ezca['VIS-'+optic+'_MN_OPTICALIGN_%s_TRAMP'%DOF] = 10.0
            ezca.switch('VIS-'+optic+'_MN_OPTICALIGN_%s'%DOF,'OFFSET','ON')
            ezca['VIS-'+optic+'_MN_OPTICALIGN_%s_GAIN'%DOF] = 1.0
        lib.wait(self,ezca['VIS-'+optic+'_MN_OPTICALIGN_Y_TRAMP'])

        ## OL DCCTRL
        for DOF in ['P', 'Y']:
            ezca['VIS-'+optic+'_MN_OLDCCTRL_%s_TRAMP'%DOF] = 15
            ezca['VIS-'+optic+'_MN_OLDCCTRL_%s_GAIN'%DOF] = 1
        ezca['VIS-'+optic+'_BF_PAYOL_DCCTRL_Y_GAIN'] = 1
        ezca['VIS-'+optic+'_BF_PAYOL_OFS_Y_OFFSET'] = 0
        ezca['VIS-'+optic+'_BF_PAYOL_OFS_Y_GAIN'] = 1
	return True

class UNDAMPED(GuardState):
    index = 50
    @watchdog_check
    def run(self):
        return True


#class STRANGE_IPOFFSET(GuardState):
#    index = 54
#    request = False
#    @watchdog_check
#    def run(self):
#        if lib.check_IPdamp_OFFSET(optic,n,threshold):
#            return True

class ENGAGE_TWR_DAMPING(GuardState):
    index = 52
    request = False
    @watchdog_check
    def main(self):
        log('Turning on the damping filters')
	## IP ## (all the gains should be 1)
        for DOF in ['L','T','Y']:
            ezca['VIS-'+optic+'_IP_DAMP_%s_TRAMP'%DOF] = 60.0
            ezca['VIS-'+optic+'_IP_DAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_IP_DAMP_%s_GAIN'%DOF] = par.IPgains['%s'%DOF]
            #ezca['VIS-'+optic+'_IP_DAMP_%s_OFFSET'%DOF] = -ofsavg
	## GAS ## (zero gains for now)
        for DOF in ['BF','F3','F2','F1','F0']:
            ezca['VIS-'+optic+'_%s_DAMP_GAS_TRAMP'%DOF] = 15.0
            ezca['VIS-'+optic+'_%s_DAMP_GAS_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_%s_DAMP_GAS_GAIN'%DOF] = par.GASgains[optic]['%s'%DOF]
        lib.wait(self,ezca['VIS-'+optic+'_IP_DAMP_Y_TRAMP'])
	## BF ## (gains are decleared in BFgains individually)
        for DOF in ['L','T','V','R','P','Y']:
            ezca['VIS-'+optic+'_BF_DAMP_%s_TRAMP'%DOF] = 60.0
            #if DOF == 'Y':
            #    ezca['VIS-'+optic+'_BF_DAMP_%s_TRAMP'%DOF] = 60.0
            ezca['VIS-'+optic+'_BF_DAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_BF_DAMP_%s_GAIN'%DOF] = par.BFgains[optic]['%s'%DOF]
        lib.wait(self,ezca['VIS-'+optic+'_BF_DAMP_Y_TRAMP'])
    ## IP sensor correction ##
    # added on 2019 Aug. 13th by YF ------------------- #
        for DOF in ['X','Y']:
            ezca['VIS-'+optic+'_PEM_SEISINF_%s_RSET'%DOF] = 2
        for DOF in ['L','T']:
            ezca['VIS-'+optic+'_BF_DAMP_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_IP_SENSCORR_%s_GAIN'%DOF] = 1.0
        lib.wait(self,ezca['VIS-'+optic+'_BF_DAMP_Y_TRAMP'])
    # ------------------- #   
	return True

class TWR_DAMPED(GuardState):
    index = 55
    @watchdog_check
    def main(self):
        log(optic+"tower damped")

    @watchdog_check
    def run(self):
        return True  


class DISABLE_TWR_DAMPING(GuardState):
    index = 53
    request = False
    @watchdog_check
    def main(self):
        log('Turning off the damping filters')
        rampt_bf = 60.0
        rampt_gas = 10.0
        rampt_ip = 60.0
        rampt_ip_blend = 10.0
        lib.ip_sc_off(self, optic)
        lib.bf_damp_off(self,optic, rampt_bf)
        lib.gas_damp_off(self,optic, rampt_gas)
        lib.ip_damp_off(self,optic, rampt_ip)
        lib.ip_blend_off(self,optic, rampt_ip_blend)
	return True

    
#class ENGAGE_PAY_DAMPING(GuardState):
#    index = 520
#    request = False
#    @watchdog_check
#    def main(self):
#        TRAMP = 10
#        log('Turning on the damping filters')
#        if optic == 'ETMY':
#            ezca.switch('VIS-'+optic+'_MN_MNOLDAMP_Y','FM9','OFF')
#
#        if optic == 'ETMX':
#            ezca['VIS-'+optic+'_MN_MNOLDAMP_P_TRAMP'] = TRAMP
#            ezca['VIS-'+optic+'_MN_MNOLDAMP_P_GAIN'] = par.MNoplev_gains[optic]['P']
#        
#        ezca['VIS-' + optic + '_MN_PSDAMP_L_TRAMP'] = TRAMP
#        ezca['VIS-' + optic + '_MN_PSDAMP_L_GAIN'] = par.MNgains[optic]['L']
#        ezca['VIS-' + optic + '_IM_TMOLDAMP_P_TRAMP'] = TRAMP
#        ezca['VIS-' + optic + '_IM_TMOLDAMP_Y_TRAMP'] = TRAMP
#        ezca['VIS-' + optic + '_IM_TMOLDAMP_P_GAIN'] = par.IMoplev_gains[optic]['P']
#        ezca['VIS-' + optic + '_IM_TMOLDAMP_Y_GAIN'] = par.IMoplev_gains[optic]['Y']
#        ezca['VIS-' + optic + '_MN_TMOLDAMP_P_GAIN'] = 0
#        ezca['VIS-' + optic + '_MN_TMOLDAMP_Y_GAIN'] = 0
#        ezca['VIS-' + optic + '_TM_DAMP_P_GAIN'] = 0
#        ezca['VIS-' + optic + '_TM_DAMP_Y_GAIN'] = 0
#        ezca['VIS-' + optic + '_MN_MNOLDAMP_Y_TRAMP'] = TRAMP
#        ezca['VIS-' + optic + '_MN_MNOLDAMP_Y_GAIN'] = par.MNoplev_gains[optic]['Y']
#
#        self.timer['waiting'] = TRAMP
#
#        # BP comb setting
#        lib.clear_PAYINPUT_MTRX(optic)
#        lib.clear_PAYOUTPUT_MTRX(optic)
#
#        for ii in range(24):
#            lib.config_BPCOMB_from_description(optic = optic, DOFNUM = ii+1,
#                                           onSW = [1,2,3],TRAMP = TRAMP, LIMIT = 15000)
#
#        return True
#    @watchdog_check
#    def run(self):
#        if self.timer['waiting']:
#            return True


#class PAY_DAMPED(GuardState):
#    index = 521
#    @watchdog_check
#    def main(self):
#        log('PAYLOAD_DAMPED')
#
#    @watchdog_check
#    def run(self):
#        return True

#class DISABLE_PAY_DAMPING(GuardState):
#    index = 522
#    request = False
#    @watchdog_check
#    def main(self):
#        TRAMP = 10
#        log('Turning off the damping filter')
#        self.timer['waiting'] = TRAMP
#        ezca['VIS-' + optic + '_IM_TMOLDAMP_P_GAIN'] = 0
#        ezca['VIS-' + optic + '_IM_TMOLDAMP_Y_GAIN'] = 0
#        ezca['VIS-' + optic + '_MN_TMOLDAMP_P_GAIN'] = 0
#        ezca['VIS-' + optic + '_MN_TMOLDAMP_Y_GAIN'] = 0
#        ezca['VIS-' + optic + '_TM_DAMP_P_GAIN'] = 0
#        ezca['VIS-' + optic + '_TM_DAMP_Y_GAIN'] = 0
#        ezca['VIS-' + optic + '_MN_MNOLDAMP_P_GAIN'] = 0
#        ezca['VIS-' + optic + '_MN_MNOLDAMP_Y_GAIN'] = 0
#        ezca['VIS-' + optic + '_MN_PSDAMP_L_GAIN'] = 0
#
#        lib.disable_BPCOMB(optic)
#
#    @watchdog_check
#    def run(self):
#        if self.timer['waiting']:
#            return True



#class ENGAGE_DCCONTROL(GuardState):
#    index = 900
#    request = False
#    @watchdog_check
#    @oplev_check
#    def main(self):
#        log('Turning on the oplev controls')
#
#        ## BF ##
#        for DOF in ['L','P','Y']:
#            ezca['VIS-'+optic+'_BF_OLDAMP_%s_TRAMP'%DOF] = 5.0
#            ezca['VIS-'+optic+'_BF_OLDAMP_%s_RSET'%DOF] = 2
#            ezca['VIS-'+optic+'_BF_OLDAMP_%s_GAIN'%DOF] = par.TMoplev_BF_gains['%s'%DOF]
#            if TMoplev_BF_gains['%s'%DOF]!=0.0:
#                lib.wait(self,ezca['VIS-'+optic+'_BF_OLDAMP_%s_TRAMP'%DOF])
#	## MN ##
#        for DOF in ['L','P','Y']:
#            ezca['VIS-'+optic+'_MN_OLDAMP1_%s_TRAMP'%DOF] = 5.0
#            ezca['VIS-'+optic+'_MN_OLDAMP1_%s_RSET'%DOF] = 2
#            ezca['VIS-'+optic+'_MN_OLDAMP1_%s_GAIN'%DOF] = par.TMoplev_MN_gains['%s'%DOF]
#            if TMoplev_MN_gains['%s'%DOF]!=0.0:
#                lib.wait(self,ezca['VIS-'+optic+'_MN_OLDAMP1_%s_TRAMP'%DOF])
#	## IM ##
#            ezca['VIS-'+optic+'_IM_OLDAMP_%s_TRAMP'%DOF] = 5.0
#            ezca['VIS-'+optic+'_IM_OLDAMP_%s_RSET'%DOF] = 2
#            ezca['VIS-'+optic+'_IM_OLDAMP_%s_GAIN'%DOF] = par.TMoplev_IM_gains['%s'%DOF]
#            if TMoplev_IM_gains['%s'%DOF]!=0.0:
#                lib.wait(self,ezca['VIS-'+optic+'_IM_OLDAMP_%s_TRAMP'%DOF])
#	## TM ##
#            ezca['VIS-'+optic+'_TM_DAMP_%s_TRAMP'%DOF] = 5.0
#            ezca['VIS-'+optic+'_TM_DAMP_%s_RSET'%DOF] = 2
#            ezca['VIS-'+optic+'_TM_DAMP_%s_GAIN'%DOF] = par.TMoplev_gains['%s'%DOF]
#            if TMoplev_gains['%s'%DOF]!=0.0:
#                lib.wait(self,ezca['VIS-'+optic+'_TM_DAMP_%s_TRAMP'%DOF])
#        return True

#class DISABLE_DCCONTROL(GuardState):
#    index = 54
#    request = False
#
#    @watchdog_check
#    def main(self):
#        log('Turning off the oplev controls')
#        lib.tm_damp_off(self,optic)
#        lib.im_oldamp_off(self,optic)
#        lib.mn_oldamp_off(self,optic)
#        lib.mn_mnoldamp_off(self,optic)
#        lib.bf_oldamp_off(self,optic)
# 	return True

#class ALIGNING(GuardState):
#    index = 99
#    request = False
#    @watchdog_check
#    @oplev_check
#    def main(self):
#        log('Enabling the DC control')
#        ezca['VIS-'+ optic +'_MN_OLSET_P_TRAMP'] = 15
#        ezca['VIS-'+ optic +'_MN_OLSET_Y_TRAMP'] = 15
#        ezca['VIS-'+ optic +'_MN_OLSET_P_OFFSET'] = ezca['VIS-'+ optic +'_GOOD_OPLEV_PIT']
#        ezca['VIS-'+ optic +'_MN_OLSET_Y_OFFSET'] = ezca['VIS-'+ optic +'_GOOD_OPLEV_YAW']
#
#        for DOF in ['P','Y']:
#            #[FIXME] not cool
#            if optic in ['ITMX','ITMY','ETMY']:
#                ezca.switch('VIS-'+ optic +'_MN_OLDCCTRL_Y','OUTPUT','FM1','FM2','FM3','FM6','FM8','FM7','ON','INPUT','FM4','FM5','FM9','FM10','OFFSET','OFF')
#            else:
##                ezca.switch('VIS-'+ optic +'_MN_OLDCCTRL_Y','OUTPUT','FM1','FM2','FM3','FM4','FM8','FM9','ON','INPUT','FM5','FM6','FM7','FM10','OFFSET','OFF')
#                ezca.switch('VIS-'+ optic +'_MN_OLDCCTRL_Y','OUTPUT','FM1','FM2','FM3','FM6','FM7','FM8','ON','INPUT','FM4','FM5','FM9','FM10','OFFSET','OFF')                
#
#        ezca['VIS-'+ optic +'_MN_OLCTRL_Y_MTRX_1_1'] = 1 # MN feedback
##        ezca['VIS-'+ optic +'_MN_OLCTRL_Y_MTRX_2_1'] = 1 # BF feed-back
#
#        ezca['VIS-'+optic+'_BF_PAYOL_DCCTRL_Y_RSET'] = 2
#        ezca['VIS-'+optic+'_BF_PAYOL_DCCTRL_Y_TRAMP'] = 1
#        ezca.switch('VIS-' + optic + '_BF_PAYOL_DCCTRL_Y', 'FM1','ON')
#        ezca['VIS-'+optic+'_BF_PAYOL_DCCTRL_Y_GAIN'] = 1
#        lib.wait(self, ezca['VIS-'+optic+'_BF_PAYOL_DCCTRL_Y_TRAMP'])
#
#        ezca.switch('VIS-'+ optic +'_MN_OLDCCTRL_P','INPUT','ON')
#        ezca.switch('VIS-'+ optic +'_MN_OLDCCTRL_Y','INPUT','ON')
#        lib.wait(self, 3 * ezca['VIS-'+optic+'_MN_OLDCCTRL_Y_TRAMP'])
#        #ezca.switch('VIS-'+ optic +'_MN_OLDCCTRL_P','FM3','ON')
#        #ezca.switch('VIS-'+ optic +'_MN_OLDCCTRL_Y','FM3','ON')
#
#        #[FIXME]
#        '''
#        while not (ezca['VIS-'+optic+'_TM_OPLEV_TILT_BLRMS_Y_300M_1'] < 0.3 and abs(ezca['VIS-'+optic+'_MN_OLDCCTRL_Y_INMON']) < 1.5):
#            log('Realignment is ongoing')
#            if optic == 'ETMY':
#                ezca.switch('VIS-'+optic+'_MN_MNOLDAMP_Y','FM9','ON')
#                lib.wait(self,2)
#        '''
#        return True


class ALIGNED(GuardState):
    index = 1010
    @watchdog_check
    @oplev_check
    def main(self):
        log('ALIGNED')
    @watchdog_check
    @oplev_check
    def run(self):
        if lib.is_oplev_noisy2(optic):
            log('OpLev RMS is too large to engage OpLev damp')
            return 'ENGAGE_PAY_PS_DAMPING'
        if lib.optic_misaligned(optic):
            notify(optic+' not really aligned!')
        return True

#class FREEZING_OUTPUTS(GuardState):
#    index = 106
#    request = False
#    @watchdog_check
#    @oplev_check
#    def main(self):
#        self.TRAMP = 10
#        self.counter = 3 #leave boost on
#        log('Turning off the OLDCCTRL inputs')
#        ezca.switch('VIS-' + optic + '_MN_OLDCCTRL_Y','INPUT','OFF')
#        ezca.switch('VIS-' + optic + '_MN_OLDCCTRL_P','INPUT','OFF')
#        ezca.switch('VIS-' + optic + '_BF_PAYOL_DCCTRL_Y','INPUT','OFF')
#        self.timer['waiting'] = 0
#    @watchdog_check
#    @oplev_check
#    def run(self):
#        if self.timer['waiting']:
#            if self.counter == 1:
#                ezca.switch('VIS-'+optic+'_MN_MNOLDAMP_Y','FM9','OFF')
#                self.timer['waitinig'] = 2
#                self.counter += 1
#            elif self.counter == 2:
#                ezca['VIS-' + optic + '_MN_MNOLDAMP_Y_TRAMP'] = self.TRAMP
#                ezca['VIS-' + optic + '_MN_MNOLDAMP_Y_GAIN'] = 0.5
#                self.timer['waitinig'] = self.TRAMP
#                self.counter += 1
#            elif self.counter == 3:
#                return True


#class UNFREEZING_OUTPUTS(GuardState):
#    index = 107
#    request = False
#    @watchdog_check
#    @oplev_check
#    def main(self):
#        self.TRAMP = 10
#        self.timer['waitinig'] = 0
#        self.counter = 1
#        
#    @watchdog_check
#    @oplev_check
#    def run(self):
#        if self.timer['waitinig']:
#            if self.counter == 1:
#                ezca['VIS-' + optic + '_MN_MNOLDAMP_Y_TRAMP'] = self.TRAMP
#                ezca['VIS-' + optic + '_MN_MNOLDAMP_Y_GAIN'] = 1.0
#                self.timer['waitinig'] = self.TRAMP
#                self.counter += 1
#            elif self.counter == 2:
#                ezca.switch('VIS-'+optic+'_MN_MNOLDAMP_Y','FM9','ON')
#                self.timer['waitinig'] = 2
#                self.counter += 1
#            elif self.counter == 3:
#                log('Turning off the OLDCCTRL inputs')
#                ezca.switch('VIS-' + optic + '_MN_OLDCCTRL_Y','INPUT','ON')
#                ezca.switch('VIS-' + optic + '_MN_OLDCCTRL_P','INPUT','ON')
#                ezca.switch('VIS-' + optic + '_BF_PAYOL_DCCTRL_Y','INPUT','ON')
#                self.timer['waitnig'] = 15
#                self.counter += 1
#            elif self.counter == 4:
#                return True



#class FREEZE(GuardState):
#    index = 108
#    @watchdog_check
#    @oplev_check
#    def main(self):
#        log('FLOATING')
#    @watchdog_check
#    @oplev_check
#    def run(self):
#        return True

class MISALIGNING(GuardState):
    index = 101
    request = False
    @watchdog_check
    @oplev_check
    def main(self):
        log('Turning off the DC control, turning on the BF offset')
        ezca.switch('VIS-'+optic+'_MN_MNOLDAMP_Y','FM9','OFF')
        for DOF in ['P', 'Y']:
            ezca.switch('VIS-' + optic + '_MN_OLDCCTRL_%s'%DOF,'INPUT','OFF')

        ezca.switch('VIS-' + optic + '_BF_PAYOL_DCCTRL_Y','INPUT','OFF')

        ezca['VIS-' + optic + '_BF_PAYOL_OFS_Y_TRAMP'] = par.misalign_ramp
        ezca['VIS-' + optic + '_BF_PAYOL_OFS_Y_OFFSET'] = par.misalign_amount
        ezca.switch('VIS-' + optic + '_BF_PAYOL_OFS_Y','OFFSET','ON')
        ezca['VIS-'+optic+'_IM_TMOLDAMP_Y_GAIN'] = 0
        lib.wait(self, ezca['VIS-' + optic + '_BF_PAYOL_OFS_Y_TRAMP'])
        return True


class MISALIGNED(GuardState):
    index = 102
    @watchdog_check
    @oplev_check
    def main(self):
        log('Misaligned')
    @watchdog_check
    def run(self):
        if not lib.optic_misaligned(optic):
            notify(optic+' not really misaligned!')
        return True

class REALIGNING(GuardState):
    index = 104
    request = False
    @watchdog_check
    @oplev_check
    def main(self):
        ezca['VIS-' + optic + '_BF_PAYOL_OFS_Y_TRAMP'] = par.misalign_ramp
        ezca.switch('VIS-' + optic + '_BF_PAYOL_OFS_Y','OFFSET','OFF')
        lib.wait(self, ezca['VIS-' + optic + '_BF_PAYOL_OFS_Y_TRAMP'])

        for DOF in ['P', 'Y']:
            ezca.switch('VIS-'+ optic +'_MN_OLDCCTRL_%s'%DOF,'INPUT','ON')

        ezca['VIS-'+optic+'_IM_TMOLDAMP_Y_RSET'] = 2
        ezca['VIS-'+optic+'_IM_TMOLDAMP_Y_GAIN'] = par.IMoplev_gains[optic]['Y']
        ezca.switch('VIS-' + optic + '_BF_PAYOL_OFS_Y','INPUT','ON')
        #lib.wait(self, ezca['VIS-'+optic+'_MN_OLDCCTRL_Y_TRAMP'])
        log('Turned off the BF offset, OpLev DCCTRL ON')

        #if optic == 'ETMY':
            #ezca.switch('VIS-'+optic+'_MN_MNOLDAMP_Y','FM9','ON')
            #lib.wait(self,2)

    @watchdog_check
    @oplev_check
    def run(self):
        log('Realignment is ongoing')

        if (ezca['VIS-'+optic+'_TM_OPLEV_TILT_BLRMS_Y_300M_1'] < 0.5 and abs(ezca['VIS-'+optic+'_MN_OLDCCTRL_Y_INMON']) < 1.5):
            return True
       

#class DISABLE_MISALIGNMENT(GuardState):
#    index = 1050
#    request = False
#    @watchdog_check
#    @oplev_check
#    def main(self):
#        log('DISABLING OL DC CONTROL...')
#        ezca['VIS-' + optic + '_BF_PAYOL_OFS_Y_TRAMP'] = par.misalign_ramp
#        ezca.switch('VIS-' + optic + '_BF_PAYOL_OFS_Y','OFFSET','OFF')
#        ezca['VIS-'+optic+'_IM_TMOLDAMP_Y_RSET'] = 2
#        ezca['VIS-'+optic+'_IM_TMOLDAMP_Y_GAIN'] = 1
#        lib.wait(self, ezca['VIS-' + optic + '_BF_PAYOL_OFS_Y_TRAMP'])
#    @watchdog_check
#    @oplev_check
#    def run(self):
#        return True


#class DISABLE_DCOLCTRL(GuardState):
#    index = 1030
#    request = False
#    @watchdog_check
#    @oplev_check
#    def main(self):
#        log('DISABLING OL DC CONTROL...')
#        ezca['VIS-'+optic+'_MN_OLDCCTRL_P_TRAMP']=15
#        ezca['VIS-'+optic+'_MN_OLDCCTRL_Y_TRAMP']=15
#
#        if optic == 'ETMY':
#            ezca.switch('VIS-'+optic+'_MN_MNOLDAMP_Y','FM9','OFF')
#        lib.wait(self, 2)
#        ezca.switch('VIS-'+ optic +'_MN_OLDCCTRL_P','INPUT','OFF')
#        ezca.switch('VIS-'+ optic +'_MN_OLDCCTRL_Y','INPUT','OFF')
#        ezca.switch('VIS-'+ optic +'_BF_PAYOL_DCCTRL_Y','INPUT','OFF')
#        lib.wait(self, ezca['VIS-'+optic+'_MN_OLDCCTRL_P_TRAMP'])
#
#    @watchdog_check
#    @oplev_check
#    def run(self):
#        return True


# ------- Made by T. Ushiba 2019/8/20 -------#
#class CALM_DOWN(GuardState):
#    index = 115
#    @watchdog_check
#    @oplev_check
#    def main(self):
#        log('Payload damping is ongoing')
#    @watchdog_check
#    @oplev_check
#    def run(self):
#        if not lib.is_oplev_noisy(optic):
#            log('OpLev RMS is small sufficiently')
#            return True

#class ENGAGE_PAY_PS_DAMPING(GuardState):
#    index = 111
#    request = False
#    @watchdog_check
#    @oplev_check
#    def main(self):
#        #lib.disable_BPCOMB(optic)
#        TRAMP = 10
#        ezca['VIS-' + optic + '_MN_PSDAMP_Y_TRAMP'] = TRAMP
#        ezca['VIS-' + optic + '_MN_PSDAMP_P_TRAMP'] = TRAMP
#        ezca['VIS-' + optic + '_MN_PSDAMP_Y_GAIN'] = par.CALM_DOWN_gains[optic]['Y']
#        ezca['VIS-' + optic + '_MN_PSDAMP_P_GAIN'] = par.CALM_DOWN_gains[optic]['P']
#        #ezca.switch('VIS-'+optic+'_MN_MNOLDAMP_Y','FM9','OFF')
#        self.timer['waiting'] = TRAMP
#    @watchdog_check
#    @oplev_check
#    def run(self):
#        if self.timer['waiting']:
#            return True

#class DISABLE_PAY_PS_DAMPING(GuardState):
#    index = 112
#    request = False
#    @watchdog_check
#    @oplev_check
#    def main(self):
#        TRAMP = 10
#        ezca['VIS-' + optic + '_MN_PSDAMP_Y_TRAMP'] = TRAMP
#        ezca['VIS-' + optic + '_MN_PSDAMP_P_TRAMP'] = TRAMP
#        ezca['VIS-' + optic + '_MN_PSDAMP_Y_GAIN'] = 0
#        ezca['VIS-' + optic + '_MN_PSDAMP_P_GAIN'] = 0
#        
#        #lib.clear_PAYINPUT_MTRX(optic)
#        #lib.clear_PAYOUTPUT_MTRX(optic)
#
#        #for ii in range(24):
#        #    lib.config_BPCOMB_from_description(optic = optic, DOFNUM = ii+1,
#        #                                   onSW = [1,2,3],TRAMP = TRAMP, LIMIT = 15000)
#
#        self.timer['waiting'] = TRAMP
#
#    @watchdog_check
#    @oplev_check
#    def run(self):
#        if self.timer['waiting']:
#            return True
#--------------------------------------------#


class LOCK_AQUISITION(GuardState):
    inex = 117
    @watchdog_check
    @oplev_check
    def main(self):
        ezca.switch('VIS-'+optic+'_MN_MNOLDAMP_Y','FM9','ON')
        self.timer['waiting']=2

    @watchdog_check
    @oplev_check
    def run(self):
        if self.timer['waiting']:
            return True


##################################################
# Edges

edges = [
    ('INIT','SAFE'),
    ('RESET', 'SAFE'),
    ('TRIPPED','SAFE'),
    ('PAY_TRIPPED','TWR_DAMPED'),
    ('SAFE','OUTPUT_ON'),
    ('OUTPUT_ON','UNDAMPED'),
    ('UNDAMPED','ENGAGE_TWR_DAMPING'),
    ('ENGAGE_TWR_DAMPING','TWR_DAMPED'),
    ('TWR_DAMPED','ENGAGE_PAY_DAMPING'),
    ('ENGAGE_PAY_DAMPING','PAY_DAMPED'),
    ('PAY_DAMPED','DISABLE_PAY_DAMPING'),
    ('DISABLE_PAY_DAMPING','TWR_DAMPED'),
    ('TWR_DAMPED','DISABLE_TWR_DAMPING'),
    ('DISABLE_TWR_DAMPING','UNDAMPED'),
    ('UNDAMPED','SAFE'),
    ('PAY_DAMPED','ALIGNING'),
    ('ALIGNING','ALIGNED'),
    ('ALIGNED','DISABLE_DCOLCTRL'),
    ('DISABLE_DCOLCTRL','PAY_DAMPED'),
    ('ALIGNED','MISALIGNING'),
    ('MISALIGNING','MISALIGNED'),
    ('MISALIGNED','REALIGNING'),
    ('REALIGNING','ALIGNED'),
    ('MISALIGNED','DISABLE_MISALIGNMENT'),
    ('DISABLE_MISALIGNMENT','PAY_DAMPED'),
    ('PAY_DAMPED','MISALIGNING'),
    ('ALIGNED','FREEZING_OUTPUTS'),
    ('FREEZING_OUTPUTS','FREEZE'),
    ('FREEZE','UNFREEZING_OUTPUTS'),
    ('UNFREEZING_OUTPUTS','ALIGNED'),
    ('FREEZE','DISABLE_DCOLCTRL'),
    ('ENGAGE_PAY_PS_DAMPING','CALM_DOWN'),
    ('CALM_DOWN','DISABLE_PAY_PS_DAMPING'),
    ('DISABLE_PAY_PS_DAMPING','ALIGNED'),
    ('ALIGNED','LOCK_AQUISITION')
   ]
