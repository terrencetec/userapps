import threading
import subprocess
import argparse
import ezca
import time

# ------------------------------------------------------------------------------    
def run_diag(fname):
    ''' Run shell command which executes the diaggui xml file.

    This function runs the diaggui file and output some files;
     * './log/tmp_*_in' is a command file to execute via diag command,
     * './log/tmp*_out' is a stdout file for shell command,
     * './log/tmp*_err' is a stderr file for shell command.

    Parameters
    ----------
    fname: `str`
        File name of the diaggui xml file.

    '''
    _fname = fname.split('/')[3].replace('.xml','')

    # make command file for execution
    with open('./log/tmp_{0}_in'.format(_fname),'w') as f:
        txt = 'open\nrestore {0}\nrun -w\nsave {0}\nquit\n'.format(fname)
        f.write(txt)
    print(' - Run {0}'.format(fname))
    
    # run diag command with command file
    with open('./log/tmp_{0}_in'.format(_fname),'r') as tmp_in:
        with open('./log/tmp_{0}_out'.format(_fname),'w') as tmp_out:
            with open('./log/tmp_{0}_err'.format(_fname),'w') as tmp_err:
                ret = subprocess.run('diag',
                                     shell=True,
                                     check=True,
                                     stdin=tmp_in,
                                     stdout=tmp_out,
                                     stderr=tmp_err)   
    print(' - Fnished {0} {1}'.format(fname,ret))


def masterswitch_is_open(optic):
    return ezca['VIS-{0}_MASTERSWITCH'.format(optic)]==True

def is_safe(optic):
    return ezca['GRD-VIS_{0}_STATE_S'.format(optic)]=='SAFE'

def is_ready_to_measure(optic):
    if is_safe(optic) and masterswitch_is_open(optic):
        return True
    else:
        raise ValueError('Please request SAFE, and open the Master Switch.')

def get_dofs(optic,stage):
    ''' DOF list for all VIS stages
    
    This function gives DOF lists for each VIS stages.
    
    Parameters
    ----------
    optic: `str`
        optic name

    stage: `str`
        stage name

    Returns
    -------
    dofs: list
        String list of DOFs

    '''
    if stage in ['IM']:
        dofs = ['L','T','V','R','P','Y']
    elif stage in ['MN']:
        dofs = ['L','T','V','R','P','Y']        
    elif stage in ['TM']:
        dofs = ['L','P','Y']
    elif stage in ['BF']:
        if optic in ['PRM','PR2','PR3','ETMX','ITMX','ETMY','ITMY']: 
            dofs = ['L','T','V','R','P','Y']
        else:
            raise ValueError('{0} does not has the BF-damper'.format(optic))
    elif stage in ['IP']:
        dofs = ['L','T','Y']
    elif stage in ['F0','SF']:
        dofs = ['GAS']                
    elif stage in ['F1','F2','F3']:
        raise ValueError('Please choose F0 or SF if you want to measure for GAS chain')
    return dofs

def get_prefix(stage):
    '''
    '''
    if stage in ['MN','IM','TM']:
        prefix = './payload/measurements/'
    elif stage in ['BF']:
        prefix = './tower/measurements/'
    else:
        raise ValueError('{0}'.format(stage))
    return prefix

def new_fname(template,optic,stage,dof):
    _,_optic,_stage,_,_dof,_ = template.replace('.xml','').split('_')
    new = template.replace(_optic,optic).replace('_'+_dof+'_','_'+dof+'_')
    new = new.replace('_'+_dof+'_','_'+dof+'_')
    new = new.replace('_'+_stage+'_','_'+stage+'_')        
    new_fname = get_prefix(stage) + new
    return new_fname

# ------------------------------------------------------------------------------    
def run_tf_measurement(template,optic,stage,run=False):
    ''' Run diaggui xml file which measures the Transfer Function.
    
    This function runs shell command which executes the diaggui xml file for TF
    measurement. Name of the file is given by  arguments


    Parameters
    ----
    template: `str`
        name of the template diaggui file.

    target_optic: `str`
        optic name that you want to measure

    target_stage: `str`
        stage name that you want to measure

    Returns
    ----
    None
    '''
    # run diag
    prefix = get_prefix(stage)
    for dof in get_dofs(optic,stage):
        # new_fname
        fname = new_fname(template,optic,stage,dof)
        # run
        if is_ready_to_measure(optic):
            if run:
                run_diag(fname) 
        else:
            raise ValueError('!')

# ------------------------------------------------------------------------------
        
def run_copy(template,optic,stage,run=False):
    ''' Copy template file to working directory.

    This function run shell command which copies template file for TF measurement
    to measurement directory. File path to this directory is given by new_fname().
    
    Parameters
    ----------
    template: `str`
        Diaggui template file name.

    optic: `str`
        Optic name which you want to measure.

    stage: `str`
        Stage name which you want to measure.

    run: optional
        If true, execute shell command. Default is false.

    '''    
    # run command
    for dof in get_dofs(optic,stage):
        # new_fname
        _,_optic,_stage,_,_dof,_ = template.replace('.xml','').split('_')
        fname = new_fname(template,optic,stage,dof)
        # make command
        print('copy {0} -> {1}'.format(template,fname))
        cmd  = "cp -rf {0} {1}".format(template,fname)
        cmd += "; sed -i -e 's/{1}/{2}/' {0}".format(fname,_optic,optic)
        cmd += "; sed -i -e 's/TEST_{1}/TEST_{2}/' {0}".format(fname,_dof,dof)
        cmd += "; sed -i -e 's/{3}_{1}/{4}_{2}/' {0}".format(fname,_dof,dof,_stage,stage)
        cmd += "; sed -i -e 's/{1}_TEST/{2}_TEST/' {0}".format(fname,_stage,stage)
        # run
        if run:
            subprocess.run(cmd,shell=True,check=True)
        
            
if __name__=="__main__":
    ezca = ezca.Ezca(timeout=2)
    parser = argparse.ArgumentParser()
    parser.add_argument('-optics','-o',nargs='+',required=True)
    parser.add_argument('-stage','-s',nargs='+',required=True)
    parser.add_argument('--rundiag',action='store_true')
    parser.add_argument('--runcp',action='store_true')
    args = parser.parse_args()        
    runcp = args.runcp
    rundiag = args.rundiag
    
    t = []
    template = 'PLANT_PRM_IM_TEST_L_EXC.xml' # for 6 dofs stage. It takes 40 minutes
    optics = args.optics
    stage = args.stage[0]
    
    #
    # Notification
    #
    if stage not in ['IM','BF']:
        raise ValueError('{0} is not supported now.'.format(stage))
    if stage in ['IM','BF','MN']: # for 6 dofs stage
        if template.split('_')[2] not in ['IM','BF','MN']:        
            raise ValueError('{0} is wrong template file for 6 dofs stage.'.format(stage))
    if stage in ['MN']: # for 3 dofs stage
        if template.split('_')[2] in ['IM','BF','MN']:
            raise ValueError('{0} is wrong template file for 6 dofs stage.'.format(stage))

    #
    # Start main functions
    #
    if runcp: # Copy template file to working directory.
        for optic in optics:
            run_copy(template,optic,stage,run=True)

    if rundiag: # Parallel measurement for each optics!
        for optic in optics:
            _t = threading.Thread(target=run_tf_measurement,args=(template,optic,stage),kwargs={'run':True})
            _t.start()
            #_t.join()
            t += [_t]
