from guardian import GuardState
from guardian import GuardStateDecorator

import vislib
import kagralib

import importlib
import time

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

##################################################
# Decolators
class check_WD(GuardStateDecorator):
    #[FIXME] decorator to check WDs
    def pre_exec(self):
        pass

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
    def main(self):
        ezca['VIS-%s_MASTERSWITCH'%OPTIC] = 1
    
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

        self.engagelist = {'IP':['LEN','TRA','YAW'],
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

            self.timer['waiting'] = 1
            self.counter += 1


        elif self.counter == 1:
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
            for stage in ['IP','GAS']:
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
            return True

    
    
class CLEAR_OUTPUT(GuardState):
    request = False
    index = 3
    
    @is_fault    
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

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
                
            self.timer['waiting'] = max(TRAMP)
            self.counter += 1

        elif self.counter == 1:
            for stage in DCSERVO().keys():
                for DoF in DCSERVO()[stage].keys():
                    DCSERVO()[stage][DoF].RSET.put(2)
                    time.sleep(0.1)
                    DCSERVO()[stage][DoF].ramp_gain(1,0,False)
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
    def run(self):
        return True
    

class OBSERVATION(GuardState):
    request = True
    index = 1000

    pass
        
##################################################
# Edges
edges = [('INIT','SAFE'),
         ('FAULT','SAFE'),
         ('SAFE','FLOAT'),
         ('FLOAT','ENGAGE_LOCALDAMP'),
         ('ENGAGE_LOCALDAMP','ENGAGE_TWRDC'),
         ('ENGAGE_TWRDC','ENGAGE_OPAL'),
         ('ENGAGE_OPAL','LOCALDAMPED'),
         ('LOCALDAMPED','ENGAGE_OLSERVO'),
         ('ENGAGE_OLSERVO','OLDAMPED'),
         ('OLDAMPED','ENGAGE_OLDC'),
         ('ENGAGE_OLDC','ALIGNED'),
         ('ALIGNED','ENGAGE_HBWOLDC'),
         ('ENGAGE_HBWOLDC','HBW_OLDC'),
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
         ('CLEAR_OUTPUT','SAFE'),
         ]
