import sys
sys.path.append('/opt/rtcds/userapps/release/vis/common/scripts/automeasurement')
sys.path.append('/usr/lib/python3/dist-packages')
from plot import plot
import numpy as np
import ezca

#import ROOT
import foton

ezca = ezca.Ezca(timeout=2)

def read_multi(chnames):
    '''
    '''
    chnames = np.array(chnames)
    if len(chnames.shape)==1:
        data = [ezca[chname] for chname in chnames]
    elif len(chnames.shape)==2:
        data = [[ezca[col] for col in chname] for chname in chnames]
    else:
        raise ValueError('!')
    data = np.array(data)
    return data

def save_params(fname,chnames,data):
    '''
    '''
    np.savetxt(fname,np.vstack([chnames,data]).T,fmt='%s')    
    
def read_params(fname):
    '''
    '''
    hoge = np.genfromtxt(fname,dtype='|U30')
    chnames = hoge[:,0]
    data = hoge[:,1].astype(float)
    return chnames,data

def sensor_name(stage):
    '''
    '''
    if stage=='IM':
        sensor = 'OSEM'
    elif stage=='BF':
        sensor = 'LVDT'
    else:
        raise ValueError('!')    
    return sensor


def main1():    
    sixinf_ofst = 'VIS-{o}_{s}_{sens}INF_{dof}_OFFSET'
    sixinf_gain = 'VIS-{o}_{s}_{sens}INF_{dof}_GAIN'
    sixsensmat = 'VIS-{o}_{s}_{sens}2EUL_{r}_{c}'
    sixsensmat = 'VIS-{o}_{s}_{sens}2EUL_{r}_{c}'
    sixsensalgn = 'VIS-{o}_{s}_SENSALIGN_{r}_{c}'
    sixactmat = 'VIS-{o}_{s}_EUL2COIL_{r}_{c}'
    #
    sens6dofs = ['V1','V2','V3','H1','H2','H3']
    eul6dofs = ['L','T','V','R','P','Y']    
    #
    optics = ['PRM','PR2','PR3']
    stages = ['IM','BF']
    save = True
    write = True
    for optic in optics:
        for stage in stages:
            if save:            
                # Read parameters from EPICS
                sensor = sensor_name(stage)
                chnames = [sixinf_ofst.format(o=optic,s=stage,sens=sensor,dof=dof)
                           for dof in sens6dofs]
                chnames += [sixinf_gain.format(o=optic,s=stage,sens=sensor,dof=dof)
                            for dof in sens6dofs]
                _chnames = [sixsensmat.format(o=optic,s=stage,sens=sensor,r=r,c=c)
                            for r in range(1,7) for c in range(1,7)]
                chnames += list(map(lambda x: x.replace('LVDT','SENS'),_chnames)) # Need fix in RTM
                chnames += [sixsensalgn.format(o=optic,s=stage,r=r,c=c)
                           for r in range(1,7) for c in range(1,7)]
                _chnames = [sixactmat.format(o=optic,s=stage,r=r,c=c)
                           for r in range(1,7) for c in range(1,7)]
                chnames += list(map(lambda x: x.replace('IM_EUL2COIL','IM_EUL2OSEM'),_chnames)) # Need fix in RTM
                data = read_multi(chnames)
                
                # Save parameters to text files
                function = sensor+'INF'
                fname = '{o}_{s}_{f}.txt'.format(o=optic,s=stage,f=function)    
                save_params(fname,chnames,data)
            if write:
                # Read parameters from text files
                _chnames,_data = read_params(fname)
                for chname, value in zip(_chnames,_data):
                    print(chname,value)    

def main2():
    optics = ['PRM','PR2','PR3']
    stages = ['IM','BF']    
    sixsensmat = 'VIS-{o}_{s}_{sens}2EUL_{r}_{c}'
    for optic in optics:
        for stage in stages[1:]:
            sensor = sensor_name(stage)
            if stage=='BF':
                sensor = 'SENS'
                chnames = [[sixsensmat.format(o=optic,s=stage,sens=sensor,r=r,c=c)
                            for c in range(1,7)] for r in range(1,7)]                
            elif stage=='IM':
                chnames = [[sixsensmat.format(o=optic,s=stage,sens=sensor,r=r,c=c)
                            for c in range(1,7)] for r in range(1,7)]
                
            data = read_multi(chnames)
            print(optic,stage)
            print(data)

def copy_param(chname,target_optics):
    '''
    '''
    if type(target_optics)!=list:
        target_optics = [target_optics]
    #
    origin_optic = chname.split('-')[1].split('_')[0]
    origin_value = ezca[chname]    
    target_value = origin_value
    #
    for optic in target_optics:
        target_chname = chname.replace(origin_optic,optic)
        ezca[target_chname] = target_value
        
# ------------------------------------------------------------------------------
if __name__=='__main__':
    #main1()
    #main2()
    chname = 'VIS-PRM_IM_OSEM2EUL_5_1'
    #copy_param(chname,['PR2','PR3'])

    #import foton
    #import warnings
    #warnings.simplefilter('ignore',RuntimeWarning)
    #warnings.filterwarnings('ignore',RuntimeWarning)
    
    chans = '/opt/rtcds/kamioka/k1/chans/'
    test = foton.FilterFile(chans+'K1VISPRMT.txt')
    print(test)
    exit()
    
    stages = ['IM']
    optics = ['PRM']
    excs = ['L','T','V','R','P','Y']
    dofs = ['L','T','V','R','P','Y']
    plot(optics,stages,dofs,excs,func='DAMP',prefix='../automeasurement/current/')
