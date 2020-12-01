#
#! coding:utf-8
from guardian import GuardState
from guardian import GuardStateDecorator
from guardian import NodeManager
import vislib
import subprocess
import rcglib

# flags
eq_alert_flag = False
eq_calm_down_flag = False

# initial REQUEST state
request = 'IDLING'

# NOMINAL state, which determines when node is OK
nominal = 'ALL_ALIGNED'

# slave optics
#optics = ['PR2', 'PR3', 'SR2', 'SR3', 'BS', 'ETMX', 'ITMX', 'ETMY', 'ITMY']
optics = ['ETMX','ETMY','ITMX','ITMY','BS','SRM','SR2','SR3','PRM','PR2','PR3',
          'MCI','MCE','MCO','IMMT1','IMMT2','OMMT1','OMMT2','OSTM','TMSX','TMSY']
managed_optics = ['ETMX','ETMY','ITMX','ITMY','BS','SRM','SR2','SR3','PRM',
                  'PR2','PR3']
managed_optics = optics

nodes = NodeManager(list(map(lambda x:'VIS_'+x,managed_optics)))


# ---------
# should be moved somewhere.
models = {'ETMX':[['VISETMXT',102],['VISETMXP',103],['VISETMXMON',104],
                  ['MODALETMX',105]],
          'ETMY':[['VISETMYT',107],['VISETMYP',108],['VISETMYMON',109],
                  ['MODALETMY',110]],
          'ITMX':[['VISITMXT',92],['VISITMXP',93],['VISITMXMON',94],
                  ['MODALITMX',95]],
          'ITMY':[['VISITMYT',97],['VISITMYP',98],['VISITMYMON',99],
                  ['MODALITMY',100]],
          'BS':[['VISBST',60],['VISBSP',61]],
          'SRM':[['VISSRMT',75],['VISSRMP',76]],
          'SR2':[['VISSR2T',65],['VISSR2P',66]],
          'SR3':[['VISSR3T',70],['VISSR3P',71]],
          'PRM':[['VISPRM',55]],
          'PR2':[['VISPR2',45]],
          'PR3':[['VISPR3',50]],
          'MCI':[['VISMCI',38]],
          'MCE':[['VISMCE',39]],
          'MCO':[['VISMCO',40]],
          'IMMT1':[['VISIMMT1',42]],
          'IMMT2':[['VISIMMT2',43]],
          'OMMT1':[['VISOMMT1',80]],
          'OMMT2':[['VISOMMT2',81]],
          'OSTM':[['VISOSTM',82]],
          'TMSX':[['VISTMSX',117]],
          'TMSY':[['VISTMSY',122]]}
sus_types = {'TypeA':['ETMX','ETMY','ITMX','ITMY'],
             'TypeB':['BS','SR2','SR3','SRM'],
             'TypeBp':['PR2','PR3','PRM'],
             'TypeC':['MCI','MCO','MCE','IMMT1','IMMT2','OSTM','OMMT1','OMMT2'],
             'TypeTMS':['TMSX','TMSY']}
# ---------

def manager_request(opt,state):
    '''
    '''
    nodes['VIS_'+opt]=state

def used_optics():
    ''' Return name list of the optics which are not used someone
    
    Returns
    -------
    used : `list`
        used optics name list as the set object.
    '''
    used = [opt for opt in managed_optics if is_used(opt)]
    return used

def unused_optics():
    ''' Return name list of the optics which are not used someone
    
    Returns
    -------
    unused : `set`
        unused optics name list as the set object.
    '''
    use = []
    for opt in managed_optics:
        if is_used(opt):
            use += [opt]
    unused = set(managed_optics)-set(use)
    return unused


def is_used(opt):
    ''' check if someone use the optics

    Parameters
    ----------
    opt : `str`
        optics name.

    Returns
    -------
    flag : `Bool`
        return true if someone use.
    '''
    msg = ezca['VIS-'+opt+'_COMMISH_MESSAGE']
    button = ezca['VIS-'+opt+'_COMMISH_STATUS']
    return (msg!='') or button==1

def is_pay_localdamped(opt):
    return ezca['GRD-VIS_'+opt+'_STATE']=='PAY_LOCALDAMPED'

def is_oldamped(opt):
    return ezca['GRD-VIS_'+opt+'_STATE']=='OLDAMPED'

def is_damped(opt):
    return pay_localdamped(opt) or lodamped(opt)

def is_aligned(opt):
    return ezca['GRD-VIS_'+opt+'_STATE']=='ALIGNED' \
        or ezca['GRD-VIS_'+opt+'_STATE']=='OBSERVATION'

def _is_earthquake(seisname):
    '''
    ref [1] https://github.com/MiyoKouseki/kagra-gif/issues/112
    '''
    lolo = ezca['PEM-SEIS_{0}_GND_X_BLRMS_30MHZ100'.format(seisname)]
    low = ezca['PEM-SEIS_{0}_GND_X_BLRMS_100MHZ300'.format(seisname)]
    lolo90 = 2.7e-2 # 90th percentile of the stational seismic noise [1]
    low90 = 5.3e-1 # 90th percentile of the stational seismic noise [1]    
    return lolo>lolo90*10 and low>low90*10
    
def is_earthquake():    
    exv = _is_earthquake('EXV')
    ixv = _is_earthquake('IXV')
    eyv = _is_earthquake('EYV')

    if exv and ixv and eyv:
        return True
    else:
        return False

    
def is_there_difference():
    return True
    
class eq_check(GuardStateDecorator):
    def pre_exec(self):
        if is_earthquake():
            return 'EARTHQUAKE'

class sdf_check(GuardStateDecorator):
    def pre_exec(self):
        txt = 'SDF diff: '
        flag = True
        for optic in optics:
            for model in models[optic]:
                name, fec = model
                diffs = ezca['FEC-{fec}_SDF_DIFF_CNT'.format(fec=fec)]
                if diffs != 0:
                    txt += '{0} {1},'.format(name,int(diffs))
                    flag = False
                else:
                    pass
        if flag==False:
            notify(txt)
        
class gds_check(GuardStateDecorator):
    def pre_exec(self):
        txt = 'GDS error: '
        flag = True        
        for optic in optics:
            for model in models[optic]:
                name, fec = model
                err = ezca['FEC-{fec}_STATE_WORD'.format(fec=fec)]
                if err != 0:
                    txt += '{0} {1}, '.format(name,int(err))
                    flag = False
                else:
                    pass
        if flag==False:
            notify(txt)
        

class revive(GuardStateDecorator):
    def pre_exec(self):
        for node in nodes.get_stalled_nodes():
            node.revive()
                
        
# ------------------------------------------------------------------------------
class INIT(GuardState):
    ''' Initial State of VIS_MANAGER.

    '''
    index = 0
    goto = True
    
    def main(self):
        '''
        '''
        nodes.set_managed()
        log('set_managed')
        return True
    
        
class EARTHQUAKE(GuardState):
    index = 10
    request = False
    
    def main(self):
        global eq_alert_flag                
        # request to pay_localdamp
        ezca['GRD-LSC_LOCK_REQUEST'] = 'DOWN'
        for opt in optics:
            ezca['GRD-VIS_'+opt+'_REQUEST']='PAY_LOCALDAMPED'

        # notification
        if eq_alert_flag==True:
            text = 'Big earthquake! All suspension was automaticaly requested '\
                 + 'to PAY_LOCALDAMPED.'
            log(text)
            # ----------------------
            # alert_to_gokagra(text)
            # ----------------------
            eq_alert_flag = False
            
        # go to idling state
        ezca['GRD-VIS_MANAGER_REQUEST'] = 'IDLING'        
        self.timer['quiet'] = 1800 # wait 30 minutes. Too long?
        
    @eq_check
    def run(self):
        global eq_alert_flag
        global eq_calm_down_flag        
        # if quiet, go to idling state
        if self.timer['quiet']:
            log('Ground motion is quiet. Go to idling state.')
            eq_alert_flag = True
            eq_calm_down_flag = True
            return True

        
class IDLING(GuardState):
    index = 13
    request = True
    
    def main(self):
        # notification        
        global eq_calm_down_flag
        if eq_calm_down_flag==True:
            eq_calm_down_flag = False
            text = 'Now VIS suspensions are idling. After checking Oplev '\
                 + 'signals, please request VIS_MANAGER guardian to go '\
                 + 'ALL_ALIGN state'
            log(text)
            # ----------------------
            # alert_to_gokagra(text)
            # ----------------------
            
    @eq_check
    def run(self):
        return True

class BUILD_MODEL(GuardState):
    index = 20
    request = True
    def main(self):
        pass
        for optic in optics:
            rcglib.buildoptic(optic.lower())
            #if ezca['VIS-' + optic + '_MASTERSWITCH'] == 0:
            #    K1:VIS-TMSX_WD_RESET

    def run(self):
        ezca['GRD-VIS_MANAGER_REQUEST'] = "ALL_SAFE"
        return True
    
class XARM_READY(GuardState):
    index = 30
    request = True

    @eq_check    
    def main(self):
        ''' All suspensions are requested to ALIGNED.
        '''
        self.timer['test'] = 0
        someone_use = []        
        
    @eq_check
    @revive
    @sdf_check
    @gds_check    
    def run(self):
        '''
        Force to request the ALIGNED state if no one use the suspensions.
        '''
        # 1. Force to aligne the suspension
        someone_use = []
        misaligned_optics = ['PRM','SRM']
        aligned_optics = set(managed_optics) - set(misaligned_optics)
        for opt in aligned_optics:
            if nodes['VIS_'+opt]!='ALIGNED':
                if not is_used(opt):
                    nodes['VIS_'+opt]='ALIGNED' 
            if is_used(opt):
                someone_use += [opt]                
        for opt in misaligned_optics:
            if nodes['VIS_'+opt]!='MISALIGNED':
                if not is_used(opt):
                    nodes['VIS_'+opt]='MISALIGNED' 
            if is_used(opt):
                someone_use += [opt]                
        notify('Not managed: {0}'.format(','.join(someone_use)))            
        return True


class ALL_ALIGNED(GuardState):
    ''' Request the ALIGNED state for all suspensions.
    
    '''    
    index = 1
    request = True

    @eq_check    
    def main(self):
        '''
        '''
        self.timer['test'] = 0
                
    @eq_check
    @revive
    @sdf_check
    @gds_check    
    def run(self):
        ''' Force to request the ALIGNED state if no one use the suspensions.
        '''
        notify('Not managed: {0}'.format(','.join(used_optics())))
        optics = unused_optics()
        optics = [opt for opt in optics if nodes['VIS_'+opt]!='ALIGNED']
        [manager_request(opt,'ALIGNED') for opt in optics]
        return True

    
class ALL_SAFE(GuardState):
    ''' Request the SAFE state for all suspensions.
    
    '''    
    index = 2
    request = True

    @eq_check    
    def main(self):
        '''
        '''
        self.timer['test'] = 0
        
    @eq_check
    @revive
    @sdf_check
    @gds_check
    def run(self):
        ''' Force to request the SAFE state if no one use the suspensions.
        '''
        notify('Not managed: {0}'.format(','.join(used_optics()))) 
        optics = unused_optics()        
        optics = [opt for opt in optics if nodes['VIS_'+opt]!='SAFE']   
        [manager_request(opt,'SAFE') for opt in optics]
        return True


class ALL_LOAD(GuardState):
    ''' Load all VIS guardian
    
    '''    
    index = 8
    request = True

    @eq_check    
    def main(self):
        '''
        '''
        for optic in optics:
            ezca['GRD-VIS_%s_OP'%optic]='STOP'
        for optic in optics:
            ezca['GRD-VIS_%s_OP'%optic]='EXEC'        
        
    @eq_check
    @revive
    #@sdf_check
    #@gds_check
    def run(self):
        return True
    
    
class ALL_MISALIGNED(GuardState):
    ''' Request the ALIGNED state for all suspensions.
    
    '''    
    index = 3
    request = True

    @eq_check    
    def main(self):
        ''' All suspensions are requested to ALIGNED.
        '''
        self.timer['test'] = 0
        
    @eq_check
    @revive
    @sdf_check
    @gds_check    
    def run(self):
        ''' Force to request the MISALIGNED state if no one use the suspensions.
        '''
        notify('Not managed: {0}'.format(','.join(used_optics())))
        optics = unused_optics()
        optics = [opt for opt in optics if nodes['VIS_'+opt]!='MISALIGNED']
        [manager_request(opt,'MISALIGNED') for opt in optics]
        return True
        
    
# ------------------------------------------------------------------------------
edges = [
    ('INIT','ALL_ALIGNED'),
    ('INIT','ALL_MISALIGNED'),
    ('INIT','ALL_SAFE'),
    ('ALL_SAFE','ALL_LOAD'),
    ('ALL_LOAD','ALL_SAFE'),
    ('ALL_SAFE','BUILD_MODEL'),
    ('BUILD_MODEL','ALL_SAFE'),
    ('INIT','IDLING'),        
    ('EARTHQUAKE','IDLING'),
    ('IDLING','ALL_ALIGNED'),
    ('INIT','XARM_READY'),
]
