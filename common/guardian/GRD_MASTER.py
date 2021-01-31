import guardian
from guardian import GuardState,GuardStateDecorator
import sdflib,cdslib

__,OPTIC = SYSTEM.split('_')
#optic = OPTIC.lower()

state = 'INIT'
request = 'SAFE'
nominal = 'ALIGNED'

# --------------------------------------------------------------------
def is_isolated():
    # should read RMS value.
    l = abs(ezca['VIS-{0}_IP_IDAMP_L_INMON'.format(OPTIC)]) < 5
    t = abs(ezca['VIS-{0}_IP_IDAMP_T_INMON'.format(OPTIC)]) < 5
    y = abs(ezca['VIS-{0}_IP_IDAMP_Y_INMON'.format(OPTIC)]) < 5
    return l and t and y

def sus_type_is():
    if OPTIC in ['ETMX','ETMY','ITMX','ITMY']:
        return 'Type-A'
    elif OPTIC in ['BS','SRM','SR2','SR3']:
        return 'Type-B'
    elif OPTIC in ['PRM','PR2','PR3']:
        return 'Type-Bp'
    elif OPTIC in ['MCI','MCO','MCE','IMMT1','IMMT2']:
        return 'Type-C'
    elif OPTIC in ['OSTM','OMMT1','OMMT2']:
        return 'Type-Cp'
    else:    
        return False

def has_tower():
    if OPTIC in ['ETMX','ETMY','ITMX','ITMY',
                 'BS','SRM','SR2','SR3',
                 'PRM','PR2','PR3']:
        return True
    else:
        return False
    

def large_rms():
    return ezca['VIS-{0}_TM_WDMON_CURRENTTRIG'.format(OPTIC)]==1

def tripped():
    wd = ezca['VIS-{0}_TM_WDMON_STATE'.format(OPTIC)]==2
    dk = ezca['VIS-{0}_PAY_DACKILL_STATE'.format(OPTIC)]==0
    if has_tower():
        dk = dk or ezca['VIS-{0}_TWR_DACKILL_STATE'.format(OPTIC)]==0
        
    return wd or dk

class WDcheck(GuardStateDecorator):
    def pre_exec(self):
        if tripped():
            return 'TRIPPED'

class IsolatedCheck(GuardStateDecorator):
    def pre_exec(self):
        if not is_isolated():
            return 'ISOLATING'
        
class SAFE(GuardState):
    request = True
    index = 3

    def main(self):
        pass
    
    def run(self):
        return True

class TRIPPED(GuardState):
    request = False
    index = 2

    def main(self):
#        ezca['VIS-{0}_MASTERSWITCH'.format(OPTIC)] = 0
#        ezca['GRD-VIS_IMMT1_REQUEST'] = 'SAFE'
        pass

    def run(self):
#        if large_rms():
#            notify('Please reduce the RMS.')
#        else:
#            notify('Please release the WD and DK')
#        return not tripped()
        return True

class INIT(GuardState):
    request = True

    def main(self):
        pass

    def run(self):
        return True

class ALIGNING(GuardState):
    request = False
    index = 998
    
    @WDcheck
    def main(self):
        pass

    def run(self):
        for dof in ['P','Y']:
            filtname = 'VIS-{0}_TM_OPTICALIGN_{1}'.format(OPTIC,dof)
            filt = ezca.get_LIGOFilter(filtname)
            filt.turn_on('OFFSET')            
#            if dof=='P':
#                filt.ramp_gain(-1,0.5,False)
#            else:
#                filt.ramp_gain(1,0.5,False)
        # SDF
        fec = cdslib.ezca_get_dcuid('K1VIS'+OPTIC)
        sdflib.restore(fec,'aligned')

        return True

class DISABLE_ALIGN(GuardState):
    request = False
    index = 999

    @WDcheck
    def main(self):
        pass

    def run(self):
        for dof in ['P','Y']:
            filtname = 'VIS-{0}_TM_OPTICALIGN_{1}'.format(OPTIC,dof)
            filt = ezca.get_LIGOFilter(filtname)
            filt.turn_off('OFFSET')
#            filt.ramp_gain(0,0.5,False)
        return True

class ALIGNED(GuardState):
    request = True
    index = 1000

    @WDcheck
    def main(self):
        pass

    @WDcheck
    #@OLcheck
    def run(self):
        return True

class MISALIGNING(GuardState):
    request = False
    index = 898

    @WDcheck
    #@OLcheck    
    def main(self):
        pass

    @WDcheck
    #@OLcheck
    def run(self):
        # SDF
        fec = cdslib.ezca_get_dcuid('K1VIS'+OPTIC)
        sdflib.restore(fec,'misaligned')         
        return True

class DISABLE_MISALIGN(GuardState):
    request = False
    index = 899

    @WDcheck
    #@OLcheck    
    def main(self):
        pass

    @WDcheck
    #@OLcheck
    def run(self):
        return True

class MISALIGNED(GuardState):
    request = True
    index = 900

    @WDcheck
    #@OLcheck    
    def main(self):
        pass

    @WDcheck
    #@OLcheck
    def run(self):
        return True

class DAMPING(GuardState):
    request = False
    index = 498
    
    @WDcheck
    #@OLcheck    
    def main(self):
        pass

    @WDcheck
    #@OLcheck
    def run(self):
#        for dof in ['P','Y']:
#            filtname = 'VIS-{0}_TM_OLDCCTRL_{1}'.format('IMMT1',dof)
#            filt = ezca.get_LIGOFilter(filtname)
#            filt.turn_on('FM1')            
#            if dof=='P':
#                filt.ramp_gain(-1,0.5,False)
#            else:
#                filt.ramp_gain(1,0.5,False)
        return True

class DISABLE_DAMP(GuardState):
    request = False
    index = 499
    
    @WDcheck
    #@OLcheck    
    def main(self):
        pass

    @WDcheck
    #@OLcheck
    def run(self):
#        for dof in ['P','Y']:
#            filtname = 'VIS-{0}_TM_OLDCCTRL_{1}'.format('IMMT1',dof)
#            filt = ezca.get_LIGOFilter(filtname)
#            filt.turn_off('FM1')            
#            filt.ramp_gain(0,0.5,False)
        return True

class DAMPED(GuardState):
    request = True
    index = 500

    @WDcheck
    #@OLcheck    
    def main(self):
        pass

    @WDcheck
    #@OLcheck    
    def run(self):
        return True
    
class ISOLATING(GuardState):
    request = False
    index = 98

    @WDcheck    
    def main(self):
        self.counter = 0                
        ezca['VIS-{0}_MASTERSWITCH'.format(OPTIC)] = 1        
        pass
    
    @WDcheck
    def run(self):
        if self.counter==0:
            for dof in ['L','T','Y']:
                #filtname = 'VIS-{0}_IP_IDAMP_{1}'.format(OPTIC,dof)
                filtname = 'VIS-{0}_IP_DAMP_{1}'.format(OPTIC,dof) # for SR3
                filt = ezca.get_LIGOFilter(filtname)
                filt.turn_on('FM4','INPUT') # for miyodamp
                filt.ramp_gain(1,10,False)                
            self.counter += 1
        elif self.counter==1:
            for dof in ['L','T','Y']:
                #filtname = 'VIS-{0}_IP_IDAMP_{1}'.format(OPTIC,dof)
                filtname = 'VIS-{0}_IP_DAMP_{1}'.format(OPTIC,dof) # for SR3
                filt = ezca.get_LIGOFilter(filtname)
                filt.turn_on('FM3') # for miyodc
                #filt.ramp_gain(1,10,True)
            if is_isolated():
                return True   
        else:                        
            pass

class TO_SAFE(GuardState):
    request = False
    index = 99
    
    @WDcheck        
    def main(self):
        self.counter = 0
        self.ramp = []

    @WDcheck
    def run(self):
        if self.counter == 0:
            # SDF
            for PART in ['T','P']:
                fec = cdslib.ezca_get_dcuid('K1VIS'+OPTIC+PART)
                sdflib.restore(fec,'safe')
            self.counter += 1
            
        elif self.counter==1:
            is_ramped_count = 0
            # Fix me..
            if sus_type_is()=='Type-C':
                for dof in ['P','Y']:
                    filtname = 'VIS-{0}_TM_OPTICALIGN_{1}'.format(OPTIC,dof)
                    filt = ezca.get_LIGOFilter(filtname)
                    if filt.is_offset_ramping() == False:
                        is_ramped_count += 1
                if is_ramped_count == 2:
                    # Disconnect the master switch after ramping.
                    ezca['VIS-{0}_MASTERSWITCH'.format(OPTIC)] = 0
                    return True                
            elif sus_type_is()=='Type-B':
                log('!!!!')
                for dof in ['L','T','Y']:
                    filtname = 'VIS-{0}_IP_IDAMP_{1}'.format(OPTIC,dof)
                    filt = ezca.get_LIGOFilter(filtname)
                    filt.ramp_gain(0,30,False)
                    
                for dof in ['L','T','Y']:
                    filtname = 'VIS-{0}_IP_IDAMP_{1}'.format(OPTIC,dof)
                    filt = ezca.get_LIGOFilter(filtname)
                    if not filt.is_gain_ramping():
                        filt.turn_off('FM3','FM4') # for miyodc

                ramp = []
                for dof in ['L','T','Y']:
                    filtname = 'VIS-{0}_IP_IDAMP_{1}'.format(OPTIC,dof)
                    filt = ezca.get_LIGOFilter(filtname)
                    ramp += [not filt.is_gain_ramping()]
                if all(ramp):
                    self.counter += 1
        elif self.counter==2:
            ezca['VIS-{0}_MASTERSWITCH'.format(OPTIC)] = 0
            return True
        else:
            pass


class ISOLATED(GuardState):
    request = True
    index = 100

    @WDcheck        
    def main(self):
        pass  

    @WDcheck
    @IsolatedCheck
    def run(self):
        return True    
    
edges = [('INIT','SAFE'),
         ('DAMPED','ALIGNING'),
         ('ALIGNING','ALIGNED'),
         ('ALIGNED','DISABLE_ALIGN'),
         ('DISABLE_ALIGN','DAMPED'),
         ('DAMPED','MISALIGNING'),
         ('MISALIGNING','MISALIGNED'),
         ('MISALIGNED','DISABLE_MISALIGN'),
         ('DISABLE_MISALIGN','DAMPED'),         
         ('ISOLATED','DAMPING'),
         ('DAMPING','DAMPED'),
         ('DAMPED','DISABLE_DAMP'),
         ('DISABLE_DAMP','ISOLATED'),
         ('SAFE','ISOLATING'),
         ('ISOLATING','ISOLATED'),
         ('ISOLATED','TO_SAFE'),
         ('TO_SAFE','SAFE'),
         ('TRIPPED','TO_SAFE'),         
]
