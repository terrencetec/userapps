from guardian import GuardState,GuardStateDecorator
import sdflib,cdslib

optic = 'IMMT1'

state = 'INIT'
request = 'SAFE'
nominal = 'ALIGNED'

def large_rms():
    return ezca['VIS-{0}_TM_WDMON_CURRENTTRIG'.format(optic)]==1

def tripped():
    wd = ezca['VIS-{0}_TM_WDMON_STATE'.format(optic)]==2
    dk = ezca['VIS-{0}_DACKILL_STATE'.format(optic)]==0
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
        ezca['VIS-{0}_MASTERSWITCH'.format(optic)] = 0
        ezca['GRD-VIS_IMMT1_REQUEST'] = 'SAFE'

    def run(self):
        if large_rms():
            notify('Please reduce the RMS.')
        else:
            notify('Please release the WD and DK')
        return not tripped()
    
class INIT(GuardState):
    request = True    
    def main(self):
        pass
    

class ALIGNING(GuardState):
    request = False
    index = 998
    
    @WDcheck
    def main(self):
        for dof in ['P','Y']:
            filtname = 'VIS-{0}_TM_OLDCCTRL_{1}'.format('IMMT1',dof)
            filt = ezca.get_LIGOFilter(filtname)
            filt.turn_on('FM2')            
            if dof=='P':
                filt.ramp_gain(-1,0.5,False)
            else:
                filt.ramp_gain(1,0.5,False)
        # SDF
        fec = cdslib.ezca_get_dcuid('K1VIS'+optic)
        sdflib.restore(fec,'aligned')
                

class DISABLE_ALIGN(GuardState):
    request = False
    index = 999
    @WDcheck
    def main(self):
        for dof in ['P','Y']:
            filtname = 'VIS-{0}_TM_OLDCCTRL_{1}'.format('IMMT1',dof)
            filt = ezca.get_LIGOFilter(filtname)
            filt.turn_off('FM2')            
            filt.ramp_gain(0,0.5,False)
            

class ALIGNED(GuardState):
    request = True
    index = 1000

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

class DISABLE_MISALIGN(GuardState):
    request = False
    index = 899
    @WDcheck
    #@OLcheck    
    def main(self):
        pass
        

class MISALIGNED(GuardState):
    request = True
    index = 900
    @WDcheck
    #@OLcheck    
    def main(self):
        pass
        
class DAMPING(GuardState):
    request = False
    index = 498
    
    @WDcheck
    #@OLcheck    
    def main(self):
        for dof in ['P','Y']:
            filtname = 'VIS-{0}_TM_OLDCCTRL_{1}'.format('IMMT1',dof)
            filt = ezca.get_LIGOFilter(filtname)
            filt.turn_on('FM1')            
            if dof=='P':
                filt.ramp_gain(-1,0.5,False)
            else:
                filt.ramp_gain(1,0.5,False)
    
class DISABLE_DAMP(GuardState):
    request = False
    index = 499
    
    @WDcheck
    #@OLcheck    
    def main(self):
        for dof in ['P','Y']:
            filtname = 'VIS-{0}_TM_OLDCCTRL_{1}'.format('IMMT1',dof)
            filt = ezca.get_LIGOFilter(filtname)
            filt.turn_off('FM1')            
            filt.ramp_gain(0,0.5,False)
    
class DAMPED(GuardState):
    request = True
    index = 500

    @WDcheck
    #@OLcheck    
    def run(self):
        return True
    
class ISOLATING(GuardState):
    request = False
    index = 98
    @WDcheck    
    def main(self):
        ezca['VIS-{0}_MASTERSWITCH'.format(optic)] = 1        
        pass

class TO_SAFE(GuardState):
    request = False
    index = 99
    
    @WDcheck        
    def main(self):
        ezca['VIS-{0}_MASTERSWITCH'.format(optic)] = 0
        # SDF
        fec = cdslib.ezca_get_dcuid('K1VIS'+optic)
        sdflib.restore(fec,'safe')                        
        return True
    

class ISOLATED(GuardState):
    request = True
    index = 100

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
