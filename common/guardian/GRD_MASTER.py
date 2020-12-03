import guardian
from guardian import GuardState,GuardStateDecorator
import sdflib,cdslib

__,OPTIC = SYSTEM.split('_')
#optic = OPTIC.lower()

state = 'INIT'
request = 'SAFE'
nominal = 'ALIGNED'

def large_rms():
    return ezca['VIS-{0}_TM_WDMON_CURRENTTRIG'.format(OPTIC)]==1

def tripped():
    wd = ezca['VIS-{0}_TM_WDMON_STATE'.format(OPTIC)]==2
    dk = ezca['VIS-{0}_DACKILL_STATE'.format(OPTIC)]==0
    return wd or dk

class WDcheck(GuardStateDecorator):
    def pre_exec(self):
        if tripped():
            return 'TRIPPED'
        
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
        pass

    @WDcheck
    def run(self):
        ezca['VIS-{0}_MASTERSWITCH'.format(OPTIC)] = 1        
        return True

class TO_SAFE(GuardState):
    request = False
    index = 99
    
    @WDcheck        
    def main(self):
        self.counter = 0

    @WDcheck
    def run(self):
        if self.counter == 0:
            # SDF
            fec = cdslib.ezca_get_dcuid('K1VIS'+OPTIC)
            sdflib.restore(fec,'safe')                        
            self.counter += 1

        else:
            is_ramped_count = 0
            for dof in ['P','Y']:
                filtname = 'VIS-{0}_TM_OPTICALIGN_{1}'.format(OPTIC,dof)
                filt = ezca.get_LIGOFilter(filtname)
                if filt.is_offset_ramping() == False:
                    is_ramped_count += 1

            if is_ramped_count == 2:
                # Disconnect the master switch after ramping.
                ezca['VIS-{0}_MASTERSWITCH'.format(OPTIC)] = 0
                return True

class ISOLATED(GuardState):
    request = True
    index = 100

    @WDcheck        
    def main(self):
        pass  

    @WDcheck        
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
