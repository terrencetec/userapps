#!/home/controls/miniconda3/envs/miyoconda37/bin/python 
#! coding:utf-8
import time
import threading
import numpy as np
import subprocess
import argparse
import ezca
import time
from plot import plot, plot_diag, plot_couple
from datetime import datetime
import os

all_optics = ['ETMX','ETMY','ITMX','ITMY',
              'BS','SRM','SR2','SR3',
              'PRM','PR2','PR3',
              'MCI','MCO','MCE','IMMT1','IMMT2',
              'OSTM','OMMT1','OMMT2']
prefix = '/opt/rtcds/userapps/release/vis/common/scripts/automeasurement'
# ------------------------------------------------------------------------------    
def run_diag(fname):
    ''' Run shell command which executes the diaggui xml file.

    This function runs the diaggui file and output some files;
     * prefix+'/log/tmp_*_in' is a command file to execute via diag command,
     * prefix+'/log/tmp*_out' is a stdout file for shell command,
     * prefix+'/log/tmp*_err' is a stderr file for shell command.

    Parameters
    ----------
    fname: `str`
        File name of the diaggui xml file.

    '''
    _fname = fname.split('/')[10].replace('.xml','')

    if not os.path.exists(fname):
        raise ValueError('{0} does not exist.'.format(fname))
    
    # make command file for execution
    with open(prefix+'/log/tmp_{0}_in'.format(_fname),'w') as f:
        txt = 'open\nrestore {0}\nrun -w\nsave {0}\nquit\n'.format(fname)
        f.write(txt)
    print(' - Run {0}'.format(fname))
    
    # run diag command with command file
    with open(prefix+'/log/tmp_{0}_in'.format(_fname),'r') as tmp_in:
        with open(prefix+'/log/tmp_{0}_out'.format(_fname),'w') as tmp_out:
            with open(prefix+'/log/tmp_{0}_err'.format(_fname),'w') as tmp_err:
                ret = subprocess.run('diag',
                                     shell=True,
                                     check=True,
                                     stdin=tmp_in,
                                     stdout=tmp_out,
                                     stderr=tmp_err)
    print(' - Fnished {0} {1}'.format(fname,ret))                
    print('Wait 30 second')
    time.sleep(30)

    archive_fname = fname
    current_fname = _fname.split('EXC')[0]+'EXC.xml' # remeove timestamp
    current_fname = prefix + '/current/' + current_fname
    cmd = 'cp {0} {1}'.format(archive_fname,current_fname)
    subprocess.run(cmd,shell=True,check=True)
    print(' -',cmd)


def open_all(optics,stages,funcs,dofs,oltf=False):
    '''
    '''
    # open LIGO Filters
    for optic in optics:
        for stage in stages:
            for func in funcs:
                for dof in dofs:
                    open_LIGOFilter(optic,stage,func,dof)
                    
    # open master switch
    for optic in optics:
        open_masterswitch(optic)
        
def available_optics(optics=all_optics):
    cms = 'VIS-{0}_COMMISH_MESSAGE'
    ok = [optic for optic in optics if ezca[cms.format(optic)]=='Miyo: SC']
    return ok

def open_LIGOFilter(optic,stage,func,dof):
    #ezca.get_LIGOFilter('VIS-{0}_{1}_{2}_{3}'.format(optic,stage,func,dof))\
    #.only_on('INPUT','OUTPUT','DECIMATION')
    #ezca['VIS-SRM_F0_TEST_GAS_GAIN'] = 1
    pass

def open_masterswitch(optic):
    ezca['VIS-{0}_PAY_MASTERSWITCH'.format(optic)]=True
    
def close_masterswitch(optic):
    ezca['VIS-{0}_PAY_MASTERSWITCH'.format(optic)]=False
    
    
def masterswitch_is_open(optic):
    return ezca['VIS-{0}_PAY_MASTERSWITCH'.format(optic)]==True

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
    elif stage in ['F0','SF','F1','F2','F3','BF',]:
        dofs = ['GAS']
    elif stage in ['F1','F2','F3']:
        raise ValueError('Please choose F0 or SF if you want to measure for GAS chain')
    return dofs

def get_prefix(stage):
    '''
    '''
    return prefix+'/archive/'

def new_fname(template,optic,stage,dof):
    '''
    '''
    _,_optic,_stage,_,_dof,_ = template.replace('.xml','').split('_')
    new = template.replace(_optic,optic).replace('_'+_dof+'_','_'+dof+'_')
    new = new.replace('_'+_dof+'_','_'+dof+'_')
    new = new.replace('_'+_stage+'_','_'+stage+'_')
    now = datetime.now().strftime('%Y%m%d%H')
    new_fname = get_prefix(stage) + new.replace('.xml','_{0}.xml'.format(now))
    return new_fname, now

# ------------------------------------------------------------------------------    
def run_tf_measurement(template,optic,stages,excs=['L','P','Y'],run=False,oltf=False,ave=5,bw=0.01):
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
    # Check if measurement is OK.
    if not is_ready_to_measure(optic):
        raise ValueError('!')
    
    # run diag
    for stage in stages:
        for dof in excs:
            # new_fname
            fname, _now = new_fname(template,optic,stage,dof)        

            # wait random time
            _t = np.random.randint(0,10,1)
            time.sleep(_t) # [sec]
            print('Wait {0} seconds to avoid confliction of other measurement.'.format(_t))
            
            # run
            if run:
                run_copy(dof,fname,template,optic,stage,excs=excs,run=True,oltf=args.oltf,ave=ave,bw=bw)
                run_diag(fname)
            else:
                raise ValueError('!')
            
    # close master_switch
    if not oltf:
        close_masterswitch(optic)

    return fname,True

# ------------------------------------------------------------------------------
        
def run_copy(dof,new_fname,template,optic,stage,excs=['L','P','Y'],run=False,oltf=False,ave=5,bw=0.01):
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
    #for dof in excs:
    # new_fname
    _,_optic,_stage,_,_dof,_ = template.replace('.xml','').split('_')
    #fname, _now = new_fname(template,optic,stage,dof)
    fname = new_fname
    # make command
    print('copy {0} -> {1}'.format(prefix+'/template/'+template,fname))
    cmd = "cp -rf {0} {1}".format(prefix+'/template/'+template,fname)
    cmd += "; sed -i -e 's/{1}_{3}_DAMP/{2}_{4}_DAMP/' {0}".\
        format(fname,_optic,optic,_stage,stage)
    cmd += "; sed -i -e 's/{1}_{3}_OLDAMP/{2}_{4}_OLDAMP/' {0}".\
        format(fname,_optic,optic,_stage,stage)        
    cmd += "; sed -i -e 's/{1}_{3}_TEST_{5}_EXC/{2}_{4}_TEST_{6}_EXC/' {0}".\
        format(fname,_optic,optic,_stage,stage,_dof,dof)
    cmd += "; sed -i -e 's/{1}_{3}_COILOUTF_{5}_EXC/{2}_{4}_COILOUTF_{6}_EXC/' {0}".\
        format(fname,_optic,optic,_stage,stage,_dof,dof)        
    cmd += "; sed -i -e 's/{1}_{3}_{5}/{2}_{4}_{6}/' {0}".\
        format(fname,_optic,optic,_stage,stage,_dof,dof)
    cmd += """; sed -i -e 's/<Param Name="Averages" Type="int">5/<Param Name="Averages" Type="int">{1}/' {0}""".format(fname,ave)
    cmd += """; sed -i -e 's/<Param Name="BW" Type="double" Unit="Hz">0.01/<Param Name="BW" Type="double" Unit="Hz">{1}/' {0}""".format(fname,bw)
    
    if oltf:
        cmd += "; sed -i -e 's/{1}_EXC/{2}_EXC/' {0}".\
            format(fname,_dof,dof)
        cmd += "; sed -i -e 's/{1}_IN1/{2}_IN1/' {0}".\
            format(fname,_dof,dof)                        
        cmd += "; sed -i -e 's/{1}_IN2/{2}_IN2/' {0}".\
            format(fname,_dof,dof)
        cmd += "; sed -i -e 's/{1}_OUT/{2}_OUT/' {0}".\
            format(fname,_dof,dof)            
    # run
    if run:
        subprocess.run(cmd,shell=True,check=True)
        if os.path.getsize(fname)<6700: # unuse
            raise ValueError('{0} is invalid file due to small file size. Please open the file by diaggui.'.format(fname))
                

# ------------------------------------------------------------------------------
if __name__=="__main__":
    ezca = ezca.Ezca(timeout=2)
    parser = argparse.ArgumentParser(
        prog='main.py',
        description='If you want to execute the template dtt file for IM stage '\
        'in PRM, PR2, and PRM, please request above command.',
        usage=prefix+'/main.py -o PRM PR2 PR3 -s IM',        
        epilog='Please bug report to Kouseki Miyo (miyo@icrr.u-tokyo.ac.jp)')
    parser.add_argument('-o',nargs='+',required=True,
                        help='Please give a name list of the optics: e.g. PRM PR2 PR3')
    parser.add_argument('-s',nargs='+',required=True,
                        help='Please give a name list of the stage: e.g. IM.')
    parser.add_argument('-d',nargs='+',required=True,
                        help='Please give a name list of the DOFs: e.g. L T V R P Y.')
    parser.add_argument('--rundiag',action='store_true',
                        help='If you execute the measurement files actualy, '\
                        'please give this option. If not, dtt template will not run.')
    parser.add_argument('--init',action='store_true',
                        help='If you want override the dtt files for actual '\
                        'measurement which is in current/* by using the '\
                        'template file in ./template/*, please give this option. '\
                        'If you do not want to override, do not give it.')
    parser.add_argument('--plot',action='store_true',
                        help='If you plot, please give this option.')
    parser.add_argument('--oltf',action='store_true',
                        help='If Open loop transfer function, please gibe this option.')
    parser.add_argument('--bw','--bandwidth',default=0.03,
                        help='')
    parser.add_argument('--ave','--average',default=10,
                        help='')        
    args = parser.parse_args()
    #
    # Arguments
    #
    optics = args.o
    stages = args.s
    excs = args.d
    optics = available_optics(optics)
    #
    if optics[0]=='all':
        optics = available_optics(optics)
        
    if stages[0]=='all':
        if excs[0]=='GAS':
            stages = ['SF','BF,''F0','F1','F2','F3']
        else:
            raise ValueError('!')
        
    if excs[0]=='all':
        if len(stages)==1 and stages[0] in ['IM','BF']:
            excs = ['L','T','V','R','P','Y']
        elif len(stages)==1 and stages[0]=='TM':
            excs = ['L','P','Y']
        else:
            raise ValueError('!')
    #
    # Notification
    #
    if len(stages)>1:
        if not 'GAS' in excs:
            raise ValueError('Please do not measure the multiple stages in same time.')
        elif 'GAS'==excs[0] and len(excs)==1:
            if all([stage in ['BF','F0','F1','F2','F3','SF'] for stage in stages]):
                template = 'PLANT_ETMY_BF_TEST_GAS_EXC.xml'
            else:
                raise ValueError('{0} does not have GAS filter.'.format(stage))
        else:
                raise ValueError('!!')            
    elif len(stages)==1:
        stage = stages[0]
        if stage=='IM':
            if args.oltf:
                template = 'OLTF_PRM_IM_TEST_L_EXC.xml'                
            else:
                template = 'PLANT_PRM_IM_TEST_L_EXC.xml'
        elif stage=='BF' and not 'GAS' in excs:        
            template = 'PLANT_PRM_BF_TEST_L_EXC.xml'
        elif stage=='TM':
            if any([ dof in ['H1','H2','H3','H4'] for dof in excs]):
                template = 'PLANT_MCO_TM_COILOUTF_H1_EXC.xml'
            else:
                template = 'PLANT_MCO_TM_TEST_P_EXC.xml'
        else:
            raise ValueError('{0}!'.format(stage))
    else:
        raise ValueError('{0}!'.format(stage))
    if not all([stage in ['IM','BF','F0','F1','F2','F3','SF','TM'] for stage in stages]):
        raise ValueError('There are stages which is not supported now in {0}'.format(stages))
    if len(optics)>3 and not args.plot:
        raise ValueError('Please reduce the number of optics because it may ' \
                         'reach to the limit of the maximum number of '\
                         'the test point. {0}'.format(optics))
    
    #
    # Start main functions
    #
    
    # Initialization
    if args.init:
        pass
        # for optic in optics:
        #     for stage in stages:
        #         run_copy(template,optic,stage,excs=excs,run=True,oltf=args.oltf)
                
    # Measurement
    if args.rundiag:
        # Time estimation
        optics_list = [optics[3*i:3*(i+1)] for i in range(4)]
        print(len(excs),float(args.ave),float(args.bw))        
        _time = int(1./float(args.bw)*float(args.ave)*len(excs)/60)# + int(0.5*len(excs))
        ans = input('It takes {0} minutes. Do you want to measure? [y/N]'.format(_time))
        if ans not in ['y','yes','Y']:
            print('You chose {0}. Stop.'.format(ans))
            exit()
        # Open the path to input the excitation signal
        funcs = ['TEST']
        if not args.oltf:
            open_all(optics,stages,funcs,excs,oltf=args.oltf)
        # Execution
        t = []                    
        for optic in optics:
            _t = threading.Thread(target=run_tf_measurement,
                                  args=(template,optic,stages),
                                  kwargs={'run':True,'excs':excs,'ave':args.ave,'bw':args.bw})
            _t.start()
            t += [_t]
      
    # Plot
    if args.plot:
        if not stage in ['TM']:
            func = 'DAMP'
        else:
            func = 'OLDAMP'
        
        if any([ dof in ['L','T','V','P','Y','R'] for dof in excs]):
            test = 'TEST'
            dofs = excs
        elif any([ dof in ['H1','H2','H3','H4'] for dof in excs]):            
            test = 'COILOUTF'
            dofs = ['P','Y']
        else:
            raise ValueError('!')

                
        if test=='COILOUTF':
            for dof in dofs:
                plot(optics,stages,dof,excs,func=func,oltf=args.oltf,test=test,diag='diag')
        elif test=='TEST':
            plot(optics,stages,dofs,excs,func=func,oltf=args.oltf,test=test,diag='diag')
            plot_couple(optics,stages,excs,excs,func=func)  
