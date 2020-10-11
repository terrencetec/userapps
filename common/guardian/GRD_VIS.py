from guardian import GuardState
from guardian import GuardStateDecorator

import vislib
import kagralib

import importlib
import time
import numpy as np

sysmod = importlib.import_module(SYSTEM)

__,OPTIC = SYSTEM.split('_') # This instruction retrieves the name of the Guardian node running the code e.i. the suspension name: SYSTEM='VIS_BS'.
optic = OPTIC.lower()
sustype = vislib.get_Type(OPTIC)


##################################################
# initialization values
state = 'INIT' # For determining where the guardian state is.

# initial REQUEST state
request = 'INIT'

# NOMINAL state, which determines when node is OK
nominal = 'OBSERVATION'

##################################################
# Utility functions
##################################################
def is_oplev_outofrange():
    return ezca['MOD-%s_DIAG_OL_PROC_TM_TILT_SUM_OUTPUT'%OPTIC] < sysmod.OPLEV_SUM_THR

def is_IPoutput_large():
    #[FIXME] return True if IP output is close to satulation
    return False

def lost():
    # [FIXME]if suspension is totally off, return True
    return False

def check_fault():
    flag = False
    msg = 'Check ['
    if lost():
        flag = True
        msg += 'suspension status, '
        
    msg += ']'

    return flag,msg

##################################################
# LIGO Filter objects
##################################################
def DCSERVO():
    DCSERVO = {
        'MN': {DoF:ezca.get_LIGOFilter('MOD-%s_TMOL_DC_MN_%s'%(OPTIC,DoF)) for DoF in ['PIT','YAW']},
        'BF': {DoF:ezca.get_LIGOFilter('MOD-%s_TMOL_DC_BF_%s'%(OPTIC,DoF)) for DoF in ['YAW',]},
        'IP': {DoF:ezca.get_LIGOFilter('MOD-%s_IPDC_%s'%(OPTIC,DoF)) for DoF in ['LEN','TRA','YAW']},
        'GAS': {DoF:ezca.get_LIGOFilter('MOD-%s_GASDC_%s'%(OPTIC,DoF)) for DoF in ['F0','F1','F2','F3','BF']},
    }
    return DCSERVO

def DAMPSERVO():
    DAMPSERVO = {
        stage: {DoF: ezca.get_LIGOFilter('MOD-%s_DAMP_%s_%s'%(OPTIC,stage,DoF)) for DoF in ['LEN','TRA','VER','ROL','PIT','YAW']} for stage in ['IP','BF','MN','IM','TM']
    }
    DAMPSERVO['GAS'] = {DoF: ezca.get_LIGOFilter('MOD-%s_DAMP_GAS_%s'%(OPTIC,DoF)) for DoF in ['M%d'%ii for ii in range(1,6)]}

    return DAMPSERVO

def OPAL():
    OPAL = {
        stage:{ DoF:ezca.get_LIGOFilter('MOD-%s_TMOL_OPAL_%s_%s'%(OPTIC,stage,DoF)) for DoF in ['PIT','YAW']}
        for stage in ['BF','MN']
    }
    return OPAL

def ISC():
    ISC = {
        filt:{DoF:ezca.get_LIGOFilter('MOD-%s_ISC_%s_%s'%(OPTIC,filt,DoF)) for DoF in ['LEN','PIT','YAW']} for filt in ['COM1','COM2','COM3','BF','MN','IM','TM','FB_MN','FB_IM','FB_TM']
    }
    return ISC
##################################################
# Decolators
class check_iscWD(GuardStateDecorator):
    #[FIXME] decorator to check WDs
    def pre_exec(self):
        for DoF in ['LEN','PIT','YAW']:
            for stage in ['BF','MN','IM','TM']:
                if ezca['MOD-%s_ISC_WD_%s_%s_STATE'%(OPTIC,stage,DoF)]:
                    kagralib.speak_aloud('%s ISC watch dog has been tripped.'%OPTIC)
                    return 'CLEAR_ISCWD'

class is_fault(GuardStateDecorator):
    def pre_exec(self):
        flag, _ = check_fault()
        if flag:
            if ezca['GRD-NEW_%s_STATE'%OPTIC] == 'SAFE':
                return 'FAULT'
            
            ezca['GRD-NEW_%s_REQUEST'%OPTIC] = 'SAFE'
            
        

##################################################
# State Definitions
class INIT(GuardState):
    request = True
    def run(self):
        return True

class FAULT(GuardState):
    request = False
    def run(self):
        flag, msg = check_fault()
        if flag:
            notify(msg)
        else:
            return True

class SAFE(GuardState):
    request = True
    index = 1

    def is_output_off(self):
        #check output
        flag = True
        coillist = {
            stage:['H1','H2','H3','V1','V2','V3'] for stage in ['IP','BF','MN','IM','TM']
            }
        coillist['TM'] = ['H1','H2','H3','H4']

        for stage in coillist.keys():
            for coil in coillist[stage]:
                if abs(ezca['MOD-%s_COILOUT_%s_%s_OUTPUT'%(OPTIC,stage,coil)]) > 1.:
                    flag = False
        return flag

    @is_fault
    def main(self):
        self.timer['speak'] = 0

    @is_fault        
    def run(self):
        if not self.is_output_off():
            notify('CHECK OUTPUT!!!')
            if self.timer['speak']:
                kagralib.speak_aloud('%s is not safe, although safe state was requested. It has output from some coils. Please check it'%OPTIC)
                self.timer['speak'] = 300

        else:
            ezca['VIS-%s_MASTERSWITCH'%OPTIC] = 0
            return True

class FLOAT(GuardState):
    request = True
    index = 5
    
    @is_fault
    def run(self):
        return True

class ENGAGE_LOCALDAMP(GuardState):
    request = False
    index = 10
    
    @is_fault
    def main(self):
        self.timer['waiting'] = 0
        self.counter = 0

        self.engagelist = {#'IP':['LEN','TRA','YAW'],
                           'BF':['YAW'],
                           }

    @is_fault        
    def run(self):
        if not self.timer['waiting']:
            return
        
        if self.counter == 0:
            for stage in self.engagelist.keys():
                for DoF in self.engagelist[stage]:
                    DAMPSERVO()[stage][DoF].ramp_gain(1,1,False)

            try:
                for DoF in sysmod.GASDAMP_LIST:
                    ezca.get_LIGOFilter('MOD-%s_DAMP_GAS_%s'%(OPTIC,DoF)).ramp_gain(1,1,False)
            except NameError:
                pass
            ezca.get_LIGOFilter('MOD-%s_DAMP_MN_LEN'%OPTIC).ramp_gain(0.3,1,False)
            ezca.get_LIGOFilter('MOD-%s_DAMP_MN_TRA'%OPTIC).ramp_gain(0.3,1,False)
            self.timer['waiting'] = 1
            self.counter += 1


        elif self.counter == 1:
            for DoF in ['L','T','Y']:
                ezca.get_LIGOFilter('VIS-%s_IP_DAMP_%s'%(OPTIC,DoF)).RSET.put(2)
                time.sleep(0.3)
                ezca.get_LIGOFilter('VIS-%s_IP_DAMP_%s'%(OPTIC,DoF)).ramp_gain(1,10,False)
            self.timer['waiting'] = 10
            self.counter += 1

        else:
            return True

class ENGAGE_TWRDC(GuardState):
    request = False
    index = 20
    
    @is_fault
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

    @is_fault        
    def run(self):
        if not self.timer['waiting']:
            return

        elif self.counter == 0:
            # engage DC servo
            for stage in ['GAS']:
                for key in DCSERVO()[stage].keys():
                    DCSERVO()[stage][key].turn_on('INPUT')
                    
            self.counter += 1
            self.timer['waiting'] = 1

        elif self.counter == 1:
            return True
        
class ENGAGE_OPAL(GuardState):
    request = False
    index = 30
    
    @is_fault    
    def main(self):
        ezca['VIS-%s_MASTERSWITCH'%OPTIC] = 1
        self.counter = 0
        self.timer['waiting'] = 0

        self.unitTRAMP = 0.3 # [sec/urad] ramptime for 1 urad when zero output of DC servo when there is output. ex.) if ther is x urad output TRAMP will be x*unitTRAMP
        
    @is_fault    
    def run(self):
        if not self.timer['waiting']:
            return

        if self.counter == 0:
            TRAMP = [0,]
            
            for stage in OPAL().keys():
                for DoF in OPAL()[stage].keys():
                    offset = OPAL()[stage][DoF].OFFSET.get()
                    _TRAMP = min([self.unitTRAMP*abs(offset),30]) # if output is too large, TRAMP = 30
                    TRAMP.append(_TRAMP)
                    OPAL()[stage][DoF].ramp_gain(1,_TRAMP,False)
                    OPAL()[stage][DoF].turn_on('OFFSET')
      
            for DoF in ['L','T','Y']:
                ezca.get_LIGOFilter('VIS-%s_IP_TEST_%s'%(OPTIC,DoF)).ramp_gain(1,5,False)
                ezca.get_LIGOFilter('VIS-%s_IP_TEST_%s'%(OPTIC,DoF)).turn_on('OFFSET')
          
            self.timer['waiting'] = max(TRAMP)
            self.counter += 1

        elif self.counter == 1:
            for stage in OPAL().keys():
                for DoF in OPAL()[stage].keys():
                    OPAL()[stage][DoF].TRAMP.put(0.5)
            self.counter += 1

        elif self.counter == 2:
            return True


class DISABLE_TWRDC(GuardState):
    index = 90
    request = False

    @is_fault
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

    @is_fault
    def run(self):
        if not self.timer['waiting']:
            return

        elif self.counter == 0:
            # disable DC servo
            for stage in ['GAS','IP']:
                for key in DCSERVO()[stage].keys():
                    DCSERVO()[stage][key].turn_off('INPUT')

            self.counter += 1
            self.timer['waiting'] = 1

        elif self.counter == 1:
            return True


class DISABLE_LOCALDAMP(GuardState):
    request = False
    index = 80

    @is_fault    
    def main(self):
        self.timer['waiting'] = 0
        self.counter = 0
        
    @is_fault
    def run(self):
        if not self.timer['waiting']:
            return
        
        if self.counter == 0:
            for stage in DAMPSERVO().keys():
                log(stage)
                for DoF in DAMPSERVO()[stage].keys():
                    DAMPSERVO()[stage][DoF].ramp_gain(0,1,False)

            try:
                for DoF in sysmod.GASDAMP_LIST:
                    ezca.get_LIGOFilter('MOD-%s_DAMP_GAS_%s'%(OPTIC,DoF)).ramp_gain(0,1,False)
            except NameError:
                pass

            self.timer['waiting'] = 1
            self.counter += 1

        elif self.counter == 1:
            for DoF in ['L','T','Y']:
                ezca.get_LIGOFilter('VIS-%s_IP_TEST_%s'%(OPTIC,DoF)).ramp_offset(
                    ezca['VIS-%s_IP_SUMOUT_%s_OUTPUT'%(OPTIC,DoF)],1,False)

            for DoF in ['L','T','Y']:                
                ezca.get_LIGOFilter('VIS-%s_IP_DAMP_%s'%(OPTIC,DoF)).ramp_gain(0,10,False)
            self.timer['waiting'] = 10
            self.counter += 1

        else:
            
            return True

    
    
class CLEAR_OUTPUT(GuardState):
    request = False
    index = 3
    
    @is_fault    
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

        # offload the outputs to OPAL to make recovery easy
        self.OPALval_BFYAW = ezca['MOD-%s_SUM_BF_YAW_INMON'%OPTIC]
        self.OPALval_MNPIT = ezca['MOD-%s_SUM_MN_PIT_INMON'%OPTIC]
        self.OPALval_MNYAW = ezca['MOD-%s_SUM_MN_YAW_INMON'%OPTIC]

        self.unitTRAMP = 0.3 # [sec/urad] ramptime for 1 urad when zero output of DC servo when there is output. ex.) if ther is x urad output TRAMP will be x*unitTRAMP
        
    @is_fault    
    def run(self):
        if not self.timer['waiting']:
            return
        
        if self.counter == 0:
            # turn off output with proper ramptime. If there is output, wait until the output get 0
            TRAMP = [0,]
            for stage in DCSERVO().keys():
                for DoF in DCSERVO()[stage].keys():
                    DCSERVO()[stage][DoF].turn_off('INPUT')
                    output = DCSERVO()[stage][DoF].OUTPUT.get()
                    if output:
                        _TRAMP = min([self.unitTRAMP*abs(output),30]) # if output is too large, TRAMP = 30
                        TRAMP.append(_TRAMP)
                        DCSERVO()[stage][DoF].ramp_gain(0,_TRAMP,False)

            for stage in OPAL().keys():
                for DoF in OPAL()[stage].keys():
                    output = OPAL()[stage][DoF].OUTPUT.get()
                    _TRAMP = min([self.unitTRAMP*abs(output),30]) # if output is too large, TRAMP = 30
                    TRAMP.append(_TRAMP)
                    OPAL()[stage][DoF].ramp_gain(0,_TRAMP,False)

            for DoF in ['L','T','Y']:
                ezca.get_LIGOFilter('VIS-%s_IP_TEST_%s'%(OPTIC,DoF)).TRAMP.put(5)
                ezca.get_LIGOFilter('VIS-%s_IP_TEST_%s'%(OPTIC,DoF)).turn_off('OFFSET')
                    
            for filt in ISC().keys():
                for DoF in ISC()[filt].keys():
                    output = ISC()[filt][DoF].OUTPUT.get()
                    _TRAMP = min([self.unitTRAMP*abs(output),30]) # if output is too large, TRAMP = 30
                    TRAMP.append(_TRAMP)
                    ISC()[filt][DoF].ramp_gain(0,_TRAMP,False)

                
                
            self.timer['waiting'] = max(TRAMP)
            self.counter += 1

        elif self.counter == 1:
            for stage in DCSERVO().keys():
                for DoF in DCSERVO()[stage].keys():
                    DCSERVO()[stage][DoF].RSET.put(2)
                    time.sleep(0.1)
                    DCSERVO()[stage][DoF].ramp_gain(1,0,False)
            for filt in ISC().keys():
                for DoF in ISC()[filt].keys():
                    ISC()[filt][DoF].RSET.put(2)
                    time.sleep(0.1)
                    ISC()[filt][DoF].ramp_gain(1,0,False)

            OPAL()['MN']['PIT'].ramp_offset(self.OPALval_MNPIT,0,False)
            OPAL()['MN']['YAW'].ramp_offset(self.OPALval_MNYAW,0,False)
            OPAL()['BF']['YAW'].ramp_offset(self.OPALval_BFYAW,0,False)
            self.counter += 1

        elif self.counter == 2:
            return True


class LOCALDAMPED(GuardState):
    request = True
    index = 100

    pass

class ENGAGE_OLSERVO(GuardState):
    request = False
    index = 110
    @is_fault
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0
        self.timer['speaking'] = 0
        
    @is_fault
    def run(self):
        if not self.timer['waiting']:
            return

        if self.counter == 0:
            if is_oplev_outofrange():
                if self.timer['speaking']:
                    kagralib.speak_aloud('%s optical lever is out of range. Please check it before engaging oplev damping'%OPTIC)
                    self.timer['speaking'] = 300
                return
            self.counter += 1

        elif self.counter == 1:
            OLSERVO = [ezca.get_LIGOFilter('MOD-%s_TMOL_SERVO_MN_PIT'%OPTIC),
                       ezca.get_LIGOFilter('MOD-%s_MNOL_SERVO_MN_YAW'%OPTIC)]
            try:
                for mode in sysmod.DAMPMODE_LIST:
                    OLSERVO.append(ezca.get_LIGOFilter('MOD-%s_MODE%d_SERVO'%(OPTIC,mode)))
            except NameError:
                pass
            
            for servo in OLSERVO:
                servo.ramp_gain(1,1,False)

            self.timer['waiting'] = 1
            self.counter += 1

        elif self.counter == 2:
            return True


class DISABLE_OLSERVO(GuardState):
    request = False
    index = 190
    
    @is_fault
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0
        
    @is_fault
    def run(self):
        if not self.timer['waiting']:
            return

        if self.counter == 0:
            OLSERVO = [ezca.get_LIGOFilter('MOD-%s_TMOL_SERVO_MN_PIT'%OPTIC),
                       ezca.get_LIGOFilter('MOD-%s_MNOL_SERVO_MN_YAW'%OPTIC)]
            try:
                for mode in sysmod.DAMPMODE_LIST:
                    OLSERVO.append(ezca.get_LIGOFilter('MOD-%s_MODE%d_SERVO'%(OPTIC,mode)))
            except NameError:
                pass
            
            for servo in OLSERVO:
                servo.ramp_gain(0,1,False)

            self.timer['waiting'] = 3
            self.counter += 1

        elif self.counter == 1:
            return True


class OLDAMPED(GuardState):
    request = True
    index = 200
    
    @check_iscWD    
    @is_fault
    def run(self):
        return True

    
class ENGAGE_OLDC(GuardState):
    request = False
    index = 210

    def is_close_enough(self):
        #[FIXME] return True if the suspension angle is close enough to setpoint
        return True
    
    @is_fault
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

    @is_fault        
    def run(self):
        if not self.timer['waiting']:
            return

        if self.counter == 0:
            # engage DC servo
            for stage in ['MN','BF']:
                for key in DCSERVO()[stage].keys():
                    DCSERVO()[stage][key].turn_on('INPUT')
                    
            self.counter += 1
            self.timer['waiting'] = 1

        elif self.counter == 1:
            return self.is_close_enough()


class DISABLE_OLDC(GuardState):
    index = 490
    request = False

    @is_fault
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

    @is_fault
    def run(self):
        if not self.timer['waiting']:
            return

        elif self.counter == 0:
            # disable DC servo
            for stage in ['MN','BF']:
                for key in DCSERVO()[stage].keys():
                    DCSERVO()[stage][key].turn_off('INPUT')

            self.counter += 1
            self.timer['waiting'] = 1

        elif self.counter == 1:
            return True

class ALIGNED(GuardState):
    index = 500
    request = True

    @is_fault
    def run(self):
        return True

class ENGAGE_HBWOLDC(GuardState):
    index = 510
    request = False

    @is_fault
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

    @is_fault
    def run(self):
        if not self.timer['waiting']:
            return

        if self.counter == 0:
            for DoF in ['PIT','YAW']:
                ezca.switch('MOD-%s_TMOL_DC_MN_%s'%(OPTIC,DoF),'FM1','FM5','ON')

            self.timer['waiting'] = 5
            self.counter += 1

        elif self.counter == 1:
            return True

class DISABLE_HBWOLDC(GuardState):
    index = 740
    request = False

    @is_fault
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

    @is_fault
    def run(self):
        if not self.timer['waiting']:
            return

        if self.counter == 0:
            for DoF in ['PIT','YAW']:
                ezca.switch('MOD-%s_TMOL_DC_MN_%s'%(OPTIC,DoF),'FM1','FM5','OFF')

            self.timer['waiting'] = 5
            self.counter += 1

        elif self.counter == 1:
            return True

class HBW_OLDC(GuardState):
    index = 750
    request = True

    @is_fault
    def main(self):
        self.avgN = 0
        self.avgval = {'PIT':0,'YAW':0}
        self.timer['averaging'] = 10

    @is_fault
    def run(self):
        if self.timer['averaging']:
            for DoF in ['PIT','YAW']:
                ezca.get_LIGOFilter('MOD-%s_ISC_OL_%s'%(OPTIC,DoF)).ramp_offset(-self.avgval[DoF]/self.avgN,0,False)
            self.avgval = {'PIT':0,'YAW':0}
            self.avgN = 0
            self.timer['averaging'] = 10

        else:
            self.avgN += 1.
            for DoF in ['PIT','YAW']:
                self.avgval[DoF] += ezca.get_LIGOFilter('MOD-%s_ISC_OL_%s'%(OPTIC,DoF)).INMON.get()
        return True


class MISALIGNING(GuardState):
    index = 760
    request = False

    @is_fault
    def main(self):
        self.OLDC = {DoF:ezca.get_LIGOFilter('MOD-%s_TMOL_DC_MN_%s'%(OPTIC,DoF)) for DoF in ['PIT','YAW']}
        self.counter = 0
        self.timer['waiting'] = 0

    @is_fault
    def run(self):
        if not self.timer['waiting']:
            return

        if self.counter == 0:
            # disable BF loop
            ezca.switch('MOD-ETMY_TMOL_DC_BF_YAW','INPUT','OFF')
            for DoF in ['YAW']:
                # decide the direction and value of misalignment.
                misal_sign = -np.sign(ezca['VIS-%s_DIAG_CAL_TM_%s_OUTPUT'%(OPTIC,DoF)])
                misal_angle = 0.8 * ezca['VIS-%s_DIAG_CAL_TM_%s_GAIN'%(OPTIC,DoF)]
                if self.OLDC[DoF].is_off('OFFSET'):
                    self.OLDC[DoF].ramp_offset(0,0,False)
                    self.OLDC[DoF].turn_on('OFFSET')
                ofsvalue = -misal_sign*misal_angle + ezca['MOD-%s_TMOL_DC_SETPOINT_%s_OFFSET'%(OPTIC,DoF)]
                self.OLDC[DoF].ramp_offset(ofsvalue,5,False)
            self.timer['checking'] = 3
            self.counter += 1

        elif self.counter == 1:
            # if oplev value is close enough to the misal position return True
            if not all([abs(self.OLDC[DoF].INMON.get()+self.OLDC[DoF].OFFSET.get())<5 for DoF in ['PIT','YAW']]):
                self.timer['checking'] = 3
                
            if self.timer['checking']:
                return True

class MISALIGNED(GuardState):
    index = 770
    request = True

    @is_fault
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

    @is_fault
    def run(self):
        if self.counter == 0:
            kagralib.speak_aloud('%s has been misaligned'%OPTIC)
            self.counter += 1

        else:
            return True
            
class REALIGNING(GuardState):
    index = 780
    request = False

    @is_fault
    def main(self):
        self.OLDC = {DoF:ezca.get_LIGOFilter('MOD-%s_TMOL_DC_MN_%s'%(OPTIC,DoF)) for DoF in ['PIT','YAW']}
        self.counter = 0
        self.timer['waiting'] = 0

    @is_fault
    def run(self):
        if not self.timer['waiting']:
            return

        if self.counter == 0:

            for DoF in ['YAW']:
                self.OLDC[DoF].ramp_offset(0,5,False)
            self.timer['checking'] = 3
            self.counter += 1

        elif self.counter == 1:
            # if oplev value is close enough to the nomisal position return True
            if not all([abs(self.OLDC[DoF].INMON.get()+self.OLDC[DoF].OFFSET.get())<5 for DoF in ['PIT','YAW']]):
                # engage BF loop
                ezca.switch('MOD-ETMY_TMOL_DC_BF_YAW','INPUT','ON')
                self.timer['checking'] = 3
                
            if self.timer['checking']:
                return True

class ENGAGE_LOCKAQ_OLLOOP(GuardState):
    index = 790
    request = False

    @check_iscWD
    def main(self):
        self.counter = 1 # skip averaging
        self.timer['waiting'] = 0
        self.OLY = ezca.get_LIGOFilter('MOD-%s_ISC_OL_PIT'%OPTIC)
        self.MNOLY = ezca.get_LIGOFilter('MOD-%s_ISC_MNOL_YAW'%OPTIC)
        self.OLP = ezca.get_LIGOFilter('MOD-%s_ISC_OL_YAW'%OPTIC)
        self.avgval = {'PIT':0,'YAW':0}
        self.avgN = 0
        self.timer['averaging'] = 3
        
    @check_iscWD
    def run(self):
        if not self.timer['waiting']:
            return

        if self.counter == 0:
            #average input value
            if self.timer['averaging']:
                self.OLY.ramp_offset(-self.avgval['YAW']/self.avgN,0,False)
                self.OLP.ramp_offset(-self.avgval['PIT']/self.avgN,0,False)
                time.sleep(0.1)
                self.OLP.RSET.put(2)
                self.OLY.RSET.put(2)
                self.timer['waiting'] = 0.5
                self.counter += 1
            else:
                self.avgN += 1.
                self.avgval['PIT'] += self.OLP.INMON.get()
                self.avgval['YAW'] += self.OLY.INMON.get()
                notify('averaging OL INPUT')

        elif self.counter == 1:
            # engage MNOLY and TMOLP loop
            self.MNOLY.ramp_gain(1,2,False)            
            self.OLP.ramp_gain(1,2,False)
            self.counter += 1
            self.timer['waiting'] = 3

        elif self.counter == 2:
            # engage TMOLY loop
            self.OLY.ramp_gain(1,2,False)
            # turn BF path on
            ezca.switch('MOD-%s_ISC_BF_YAW'%OPTIC,'INPUT','ON')
            self.counter += 1
            self.timer['waiting'] = 2

        else:
            return True
                

class DISABLE_LOCKAQ_OLLOOP(GuardState):
    index = 795
    request = False

    @check_iscWD
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0
        self.OLY = ezca.get_LIGOFilter('MOD-%s_ISC_OL_PIT'%OPTIC)
        self.OLP = ezca.get_LIGOFilter('MOD-%s_ISC_OL_YAW'%OPTIC)
        self.MNOLY = ezca.get_LIGOFilter('MOD-%s_ISC_MNOL_YAW'%OPTIC)
        
    @check_iscWD
    def run(self):
        if not self.timer['waiting']:
            return

        if self.counter == 0:
            # turn BF path off
            ezca.switch('MOD-%s_ISC_BF_YAW'%OPTIC,'INPUT','OFF')

            # turn off
            self.MNOLY.ramp_gain(0,2,False)
            self.OLY.ramp_gain(0,2,False)
            self.OLP.ramp_gain(0,2,False) 
            self.timer['waiting'] = 3
            self.counter += 1

        else:
            return True

        
                
class LOCK_ACQUISITION(GuardState):
    index = 800
    request = True
    
    @check_iscWD
    @is_fault
    def run(self):
        return True
    
class CLEAR_ISCWD(GuardState):
    index = 810
    request = False

    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0
        self.WDlist = {DoF: True for DoF in ['LEN','PIT','YAW']}
        
    def run(self):
        if not self.timer['waiting']:
            return

        if self.counter == 0:
            # turn olservo off
            OLSERVO = [ezca.get_LIGOFilter('MOD-%s_TMOL_SERVO_MN_PIT'%OPTIC),
                       ezca.get_LIGOFilter('MOD-%s_MNOL_SERVO_MN_YAW'%OPTIC)]
            try:
                for mode in sysmod.DAMPMODE_LIST:
                    OLSERVO.append(ezca.get_LIGOFilter('MOD-%s_MODE%d_SERVO'%(OPTIC,mode)))
            except NameError:
                pass
            
            for servo in OLSERVO:
                servo.ramp_gain(0,1,False)

            # engage PSdamp for Y, P
            ezca['MOD-%s_DAMP_MN_PIT_GAIN'%OPTIC] = 1
            ezca['MOD-%s_DAMP_MN_YAW_GAIN'%OPTIC] = 1
            
            
            # turn BF path off
            ezca.switch('MOD-%s_ISC_BF_YAW'%OPTIC,'INPUT','OFF')
            # turn LOCKAQ OL loop off
            for DoF in ['PIT','YAW']:
                OL = ezca.get_LIGOFilter('MOD-%s_ISC_OL_%s'%(OPTIC,DoF))
                OL.ramp_gain(0,0,False)
            MNOLY = ezca.get_LIGOFilter('MOD-%s_ISC_MNOL_YAW'%OPTIC)
            MNOLY.ramp_gain(0,2,False)
            ezca.get_LIGOFilter('MOD-%s_TMOL_SERVO_TM_YAW'%OPTIC).ramp_gain(0,2,False)
            
            # clear filter output
            for DoF in self.WDlist.keys():
                if self.WDlist[DoF]:
                    ezca.switch('MOD-%s_ISC_COM1_%s'%(OPTIC,DoF),'INPUT','OFF')
                    for fil in ['COM1','TM','COM2','IM','COM3','MN','BF']:
                        ezca['MOD-%s_ISC_%s_%s_RSET'%(OPTIC,fil,DoF)] = 2
                        time.sleep(0.2)

            self.counter += 1

        elif self.counter == 1:
            flag = True
            # check tripped WD
            for DoF in self.WDlist.keys():
                if self.WDlist[DoF]:
                    for stage in ['BF','MN','IM','TM']:
                        if ezca['MOD-%s_ISC_WD_%s_%s_STATE'%(OPTIC,stage,DoF)] == 1:
                            # if ISCWD is tripped
                            flag = False
                            if ezca['MOD-%s_ISC_WD_RMS_%s_%s'%(OPTIC,stage,DoF)] <= ezca['MOD-%s_ISC_WD_RMS_THR_%s_%s'%(OPTIC,stage,DoF)]:
                                # reset WD
                                ezca['MOD-%s_ISC_WD_%s_%s_TRAMP'%(OPTIC,stage,DoF)] = 3
                                ezca['MOD-%s_ISC_WD_%s_%s_RSET'%(OPTIC,stage,DoF)] = 1
                                time.sleep(0.1)
                                ezca['MOD-%s_ISC_WD_%s_%s_RSET'%(OPTIC,stage,DoF)] = 0
                                self.timer['checking'] = 5
                            

            if flag and self.timer['checking']:
                self.timer['check'] = 1
                self.counter += 1

                        
        elif self.counter == 2:
            # check COM input and if it is zero for 0.5 sec, turn on input switch
            for DoF in ['LEN','PIT','YAW']:
                if ezca['MOD-%s_ISC_COM1_%s_INMON'%(OPTIC,DoF)]:
                    self.timer['check'] = 0.5

            if self.timer['check']:
                self.counter += 1

        elif self.counter == 3:
            # if LOCKAQ OL loop has been turned off, return True
            flag = True
            for chan in ['MOD-%s_ISC_OL_PIT'%OPTIC,]:
                OL = ezca.get_LIGOFilter(chan)
                if kagralib.is_FM_ramping(OL):
                    flag = False
            if flag:
                for DoF in self.WDlist.keys():
                    ezca.switch('MOD-%s_ISC_COM1_%s'%(OPTIC,DoF),'INPUT','ON')
                self.counter += 1

            self.timer['OLcheck'] = 3

        elif self.counter == 4:
            # if oplev is in range for more than 3 sec, disable PS damp and return True
            if is_oplev_outofrange():
                self.timer['OLcheck'] = 3

            if self.timer['OLcheck']:
                ezca['MOD-%s_DAMP_MN_PIT_GAIN'%OPTIC] = 0
                ezca['MOD-%s_DAMP_MN_YAW_GAIN'%OPTIC] = 0
                self.counter += 1 

        else:
            return True
    
class OBSERVATION(GuardState):
    request = True
    index = 1000

    pass
        
##################################################
# Edges
edges = [('INIT','SAFE'),
         ('FAULT','SAFE'),
         ('SAFE','ENGAGE_OPAL'),
         ('ENGAGE_OPAL','FLOAT'),
         ('FLOAT','ENGAGE_LOCALDAMP'),
         ('ENGAGE_LOCALDAMP','ENGAGE_TWRDC'),
         ('ENGAGE_TWRDC','LOCALDAMPED'),
         ('LOCALDAMPED','ENGAGE_OLSERVO'),
         ('ENGAGE_OLSERVO','OLDAMPED'),
         ('OLDAMPED','ENGAGE_OLDC'),
         ('ENGAGE_OLDC','ALIGNED'),
         ('ALIGNED','ENGAGE_HBWOLDC'),
         ('ENGAGE_HBWOLDC','HBW_OLDC'),
         ('HBW_OLDC','MISALIGNING'),
         ('MISALIGNING','MISALIGNED'),
         ('MISALIGNED','REALIGNING'),
         ('REALIGNING','HBW_OLDC'),
         ('HBW_OLDC','DISABLE_HBWOLDC'),
         ('DISABLE_HBWOLDC','ALIGNED'),
         ('ALIGNED','DISABLE_OLDC'),
         ('DISABLE_OLDC','OLDAMPED'),
         ('OLDAMPED','DISABLE_OLSERVO'),
         ('DISABLE_OLSERVO','LOCALDAMPED'),
         ('LOCALDAMPED','DISABLE_TWRDC'),
         ('DISABLE_TWRDC','DISABLE_LOCALDAMP'),
         ('DISABLE_LOCALDAMP','FLOAT'),
         ('FLOAT','CLEAR_OUTPUT'),
         ('OLDAMPED','ENGAGE_LOCKAQ_OLLOOP'),
         ('ENGAGE_LOCKAQ_OLLOOP','LOCK_ACQUISITION'),
         ('LOCK_ACQUISITION','DISABLE_LOCKAQ_OLLOOP'),
         ('DISABLE_LOCKAQ_OLLOOP','OLDAMPED'),
         ('LOCK_ACQUISITION','OBSERVATION'),
         ('OBSERVATION','LOCK_ACQUISITION',),
         ('CLEAR_OUTPUT','SAFE'),
         ('CLEAR_ISCWD','LOCALDAMPED'),
         ]
