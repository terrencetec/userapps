import re
import sys
import matplotlib.pyplot as plt
from scipy import signal
sys.path.append('/opt/rtcds/userapps/release/vis/common/scripts/automeasurement')
sys.path.append('/usr/lib/python3/dist-packages')
from plot import plot
import numpy as np
import ezca
from ezca import LIGOFilter

import foton
from foton import FilterFile,Filter,iir2zpk,iir2z

ezca = ezca.Ezca(timeout=2)

chans = '/opt/rtcds/kamioka/k1/chans/'

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


all_optics = ['ETMX','ETMY','ITMX','ITMY',
              'BS','SRM','SR2','SR3',
              'PRM','PR2','PR3',
              'MCI','MCO','MCE','IMMT1','IMMT2',
              'OSTM','OMMT1','OMMT2']

def typename_is(optic):
    '''
    '''
    if optic in ['ETMX','ETMY','ITMX','ITMY']:
        return 'Type-A'
    elif optic in ['BS','SRM','SR2','SR3']:
        return 'Type-B'
    elif optic in ['PRM','PR2','PR3']:
        return 'Type-Bp'
    elif optic in ['MCI','MCO','MCE','IMMT1','IMMT2','OSTM','OMMT1','OMMT2']:
        return 'Type-C'
    else:
        raise ValueError('!')

def partname_is(optic,stage):
    '''
    '''
    if typename_is(optic) in ['Type-A','Type-B','Type-Bp']:    
        if stage in ['TM','IM','MN']:        
            part = 'P'
        elif stage in ['BF','F3','F2','F1','F0','SF','IP']:
            part = 'T'
        else:
            raise ValueError('!')
    else:
        part = ''        
    return part

def get_fm(optic,stage,func,dof):
    ''' get filter module
    '''
    chans = '/opt/rtcds/kamioka/k1/chans/'
    optic = 'PRM'
    stage = 'IM'
    part = partname_is(optic,stage)
    func = 'OSEMINF'
    dof = 'V1'
    ffname = chans+'K1VIS{0}{1}.txt'.format(optic,part)
    fmname = '{0}_{1}_{2}_{3}'.format(optic,stage,func,dof)
    _ff = foton.FilterFile(ffname)    
    _fm = _ff[fmname]
    return _ff,_fm

class Ezff(FilterFile):
    def __init__(self,ffname):        
        super().__init__(ffname)
        self.ffname = ffname

    def save(self):
        self.ff.write(self.ffname)


def foton2zpk(zpkstr):
    '''
    '''
    zpkstr = str(zpkstr)
    result = re.findall('zpk\(\[(.*)\],\[(.*)\],(.*),"f"\)',zpkstr)[0]
    z,p,k = [map(eval,item.replace('i','1j').split(';')) if item!='' else [] for item in result]
    return list(z),list(p),list(k)[0]

def db(val):
    return 20*np.log10(val)

def copy_FMs(orig,dests):
    '''
    '''
    for dest in dests:
        for i in range(10):    
            dest[i].copyfrom(orig[i])    

def init_OSEMINF(optics,stage,func='OSEMINF'):
    '''
    '''
    # Original Filter Module is given by PRM_IM
    optic = 'PRM'
    part = partname_is(optic,stage)
    ffname = chans + 'K1VIS{0}{1}.txt'.format(optic,part)
    ff = Ezff(ffname)
    fmname = '{0}_{1}_{2}_{3}'.format(optic,stage,func,'V1')
    fm_v1 = ff[fmname]
    # copy
    for optic in optics:
        part = partname_is(optic,stage)
        ffname = chans + 'K1VIS{0}{1}.txt'.format(optic,part)
        ff = Ezff(ffname)
        # copy to other FMs
        fms = []
        for dof in ['V1','V2','V3','H1','H2','H3']:
            fmname = '{0}_{1}_{2}_{3}'.format(optic,stage,func,dof)
            fms += [ff[fmname]]        
        copy_FMs(fm_v1,fms)        
        ff.save()

def all_zpk(fms,active=range(10)):
    '''
    '''
    z,p,k = [],[],1
    for i,fm in enumerate(fms):
        if i+1 in active:
            if not fm.design=='':
                huge = iir2zpk(fm,plane='f')
                _z,_p,_k = foton2zpk(huge)
                z += _z
                p += _p
                k *= _k
            else:
                pass
    return z,p,k
    
def plot_FILT(optics,stage,func='OSEMINF',fname=None,dofs=['V1','V2','V3','H1','H2','H3']):
    '''
    '''
    col = len(optics)
    fig,ax = plt.subplots(2,col,figsize=(18,6),sharex=True,sharey='row')
    fig.suptitle('Comparison of the {0}s for all DOFs'.format(func))
    for i,optic in enumerate(optics):
        part = partname_is(optic,stage)
        ffname = chans + 'K1VIS{0}{1}.txt'.format(optic,part)
        ff = Ezff(ffname)
        for dof in dofs:
            fmname = '{0}_{1}_{2}_{3}'.format(optic,stage,func,dof)
            try:
                fm = ff[fmname]
                fms = [fm[i] for i in range(10)]
                FB = ezca.get_LIGOFilter('VIS-'+fmname)
                mask = FB.get_current_swstat_mask().buttons
                mask = filter(lambda x:True if 'FM' in x else False ,mask)
                mask = map(lambda x: eval(x.replace('FM','')),mask)
                mask = list(mask)
                z,p,k = all_zpk(fms,active=mask)
                k *= ezca['VIS-'+fmname+'_GAIN']
                sys = signal.ZerosPolesGain(z,p,k)
                freq = np.logspace(-2,2,1000)            
                freq,h = signal.freqresp(sys,freq)
                #
                ax[0][i].semilogx(freq,db(np.abs(h)),label=dof)
                ax[1][i].semilogx(freq,np.rad2deg(np.angle(h)),label=dof)
            except:
                pass
        #ax[0].set_ylim(-40,20)
        ax[1][i].set_xlim(1e-2,1e2)
        ax[1][i].set_ylim(-200,200)
        ax[1][i].set_yticks(range(-180,181,90))        
        ax[0][i].legend()
        ax[1][i].set_xlabel('Frequency [Hz]')
        [[_ax.grid(which='both',color='black',linestyle=':') for _ax in __ax] for __ax in ax]
        ax[0][i].set_title('{0}_{1}'.format(optic,stage))
    ax[0][0].set_ylabel('Magnitude [dB]')
    ax[1][0].set_ylabel('Phase [deg]')        
    plt.tight_layout()
    if fname==None:
        fname = '{0}_{1}.png'.format(func,stage)
    plt.savefig(fname)
    plt.close()


def switch_on(chname,mask=['INPUT','OFFSET','OUTPUT','DECIMATION']):
    '''
    '''
    FB = ezca.get_LIGOFilter(chname)
    FMs = FB.get_current_swstat_mask().buttons
    FB.only_on(*mask)
    
    
if __name__=='__main__':
    #main1()
    #main2()
    #switch_on('VIS-PRM_IM_OSEMINF_V1',mask=['INPUT','OFFSET','FM1','FM9','OUTPUT','DECIMATION','FM8'])
    #copy_param(chname,['PR2','PR3'])

    if False:
        #plot_FILT(optics,'IM',fname='before.png')
        #init_OSEMINF(optics,'IM')
        pass
    
    if True:
        # GAS        
        optics = ['ETMX','ETMY','ITMX','ITMY','BS','SRM','SR2','SR3','PRM','PR2','PR3']
        plot_FILT(optics,'BF',func='LVDTINF',dofs=['GAS'])
        plot_FILT(optics,'SF',func='LVDTINF',dofs=['GAS'])
        plot_FILT(optics,'F0',func='LVDTINF',dofs=['GAS'])
        plot_FILT(optics,'F1',func='LVDTINF',dofs=['GAS'])
        plot_FILT(optics,'F2',func='LVDTINF',dofs=['GAS'])
        plot_FILT(optics,'F3',func='LVDTINF',dofs=['GAS'])
        plot_FILT(optics,'BF',func='COILOUTF',dofs=['GAS'])
        plot_FILT(optics,'SF',func='COILOUTF',dofs=['GAS'])
        plot_FILT(optics,'F0',func='COILOUTF',dofs=['GAS'])
        plot_FILT(optics,'F1',func='COILOUTF',dofs=['GAS'])
        plot_FILT(optics,'F2',func='COILOUTF',dofs=['GAS'])
        plot_FILT(optics,'F3',func='COILOUTF',dofs=['GAS'])        
        # IP LVDT and ACC
        optics = ['ETMX','ETMY','ITMX','ITMY','BS','SRM','SR2','SR3']        
        plot_FILT(optics,'IP',func='LVDTINF')
        plot_FILT(optics,'IP',func='ACCINF')        
        plot_FILT(optics,'IP',func='COILOUTF',dofs=['H1','H2','H3'])        
        # BF damper
        optics = ['ETMX','ETMY','ITMX','ITMY','PRM','PR2','PR3']
        plot_FILT(optics,'BF',func='LVDTINF')
        plot_FILT(optics,'BF',func='COILOUTF')
        # OSEM
        optics = ['BS','SRM','SR2','SR3','PRM','PR2','PR3']
        plot_FILT(optics,'IM')
        plot_FILT(optics,'IM',func='COILOUTF')
        # PS
        optics = ['ETMX','ETMY','ITMX','ITMY']
        plot_FILT(optics,'IM',func='OSEMINF')
        plot_FILT(optics,'MN',func='OSEMINF')
        plot_FILT(optics,'IM',func='COILOUTF')
        plot_FILT(optics,'MN',func='COILOUTF')
        # OPLEV
        optics = ['ETMX','ETMY','ITMX','ITMY','BS','SRM','SR2','SR3','PRM','PR2','PR3']
        plot_FILT(optics,'TM',func='OPLEV_TILT',dofs=['SEG1','SEG2','SEG3','SEG4'])
        plot_FILT(optics,'TM',func='OPLEV_LEN',dofs=['SEG1','SEG2','SEG3','SEG4'])
        plot_FILT(optics,'TM',func='COILOUTF',dofs=['H1','H2','H3','H4'])
        optics = ['MCI','MCE','MCO','IMMT1','IMMT2','OSTM','OMMT1','OMMT2']
        plot_FILT(optics,'TM',func='OPLEV_TILT',dofs=['SEG1','SEG2','SEG3','SEG4'])
        plot_FILT(optics,'TM',func='OSEM',dofs=['SEG1','SEG2','SEG3','SEG4'])
        plot_FILT(optics,'TM',func='COILOUTF',dofs=['H1','H2','H3','H4'])        
        exit()
        
    if False:
        stages = ['IM']
        optics = ['PRM']
        excs = ['L','T','V','R','P','Y']
        dofs = ['L','T','V','R','P','Y']
        plot(optics,stages,dofs,excs,func='DAMP',prefix='../automeasurement/current/')
