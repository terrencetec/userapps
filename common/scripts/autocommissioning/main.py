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

def _ezca(name):
    try:
        return ezca[name]
    except:
        return 0.0
    #return ezca[name]
    
def read_multi(chnames):
    '''
    '''
    chnames = np.array(chnames)
    if len(chnames.shape)==1:
        data = [_ezca(chname) for chname in chnames]
    elif len(chnames.shape)==2:
        data = [[_ezca(col) for col in chname] for chname in chnames]
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

all_typea = ['ETMX','ETMY','ITMX','ITMY']
all_typeb = ['BS','SRM','SR2','SR3']
all_typebp = ['PRM','PR2','PR3']
all_typeci = ['MCI','MCO','MCE','IMMT1','IMMT2']
all_typeco = ['OSTM','OMMT1','OMMT2']
def typename_is(optic):
    '''
    '''
    if optic in all_typea:
        return 'Type-A'
    elif optic in all_typeb:
        return 'Type-B'
    elif optic in all_typebp:
        return 'Type-Bp'
    elif optic in all_typeci or optic in all_typeco:
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

def _oplevmat(func):
    if func in ['OPLEV_TILT','OPLEV_LEN','OPLEV_ROL']:
        _mat = [[-1,-1,+1,+1],
                [+1,-1,-1,+1],
                [+1,+1,+1,+1],
                [-1,+1,-1,+1]]
    else:
        _mat = [[0,0,0,0],
                [0,0,0,0],
                [0,0,0,0],
                [0,0,0,0]]
    return _mat
        
def init_oplev(optics,stage='TM',funcs=['OPLEV_TILT']):
    '''
    '''        
    # Init each OpLev values
    for optic in optics:
        for func in funcs:        
            # Set oplev matrices
            for row in range(4):
                for col in range(4):
                    chname = 'VIS-{0}_{1}_{2}_MTRX_{3}_{4}'.format(optic,stage,func,row+1,col+1)
                    ezca[chname] = _oplevmat(func)[row][col]
            # Set -1 for gain value of QPD
            for segnum in range(4):
                chname = 'VIS-{0}_{1}_{2}_SEG{3}_GAIN'.format(optic,stage,func,segnum+1)
                ezca[chname] = -1
                
    # Init Euler matrix
    if stage=='MN':
        pass
    else:
        _oplev2eul = [[0,0,0,1],
                      [1,0,0,0],
                      [0,1,0,0]]
        _sensalign = [[1,0,0],
                      [0,1,0],
                      [0,0,1]]    
        for optic in optics:
            for row in range(3):
                for col in range(4):
                    chname = "VIS-{0}_{1}_{2}_{3}_{4}".format(optic,stage,'OPLEV2EUL',row+1,col+1)
                    ezca[chname] = _oplev2eul[row][col]
            for row in range(3):
                for col in range(3):                
                    chname = "VIS-{0}_{1}_{2}_{3}_{4}".format(optic,stage,'SENSALIGN',row+1,col+1)
                    ezca[chname] = _sensalign[row][col]               

def init_act(optics,stage='TM',func='OSEM'):
    '''
    '''        
    # Init each OpLev values
    _eul2coil = [[+1,+1,+1],
                 [+1,-1,+1],
                 [+1,-1,-1],
                 [+1,+1,-1]]
    _lkin2coil = [[+1,+1],
                  [-1,+1],
                  [-1,-1],
                  [+1,-1]]

    for optic in optics:
        for row in range(4):
            for col in range(3):
                chname = 'VIS-{0}_{1}_EUL2{2}_{3}_{4}'.format(optic,stage,func,row+1,col+1)
                ezca[chname] = _eul2coil[row][col]
    for optic in optics:
        for row in range(4):
            for col in range(2):
                chname = 'VIS-{0}_{1}_LKIN2{2}_{3}_{4}'.format(optic,stage,func,row+1,col+1)
                ezca[chname] = _lkin2coil[row][col]
                    
def init_wd(optics,stage='BF',func='WD_AC_BANDLIM_LVDT',mask=None):
    '''
    '''
    # Original Filter Module is given by PRM_IM
    optic = 'ITMY'
    part = partname_is(optic,stage)
    ffname = chans + 'K1VIS{0}{1}.txt'.format(optic,part)
    ff = Ezff(ffname)
    if stage in ['F0','F1','F2','F3','SF']:
        fmname = '{0}_{1}_{2}_{3}'.format(optic,stage,func,'GAS')
    elif stage in ['IM','IP','BF']:
        fmname = '{0}_{1}_{2}_{3}'.format(optic,stage,func,'H1')
    elif stage in ['TM']:
        fmname = '{0}_{1}_{2}_{3}'.format(optic,stage,func,'SEG1')
    else:
        raise ValueError('!')
    fm_v1 = ff[fmname]
    # copy
    for optic in optics:
        part = partname_is(optic,stage)
        ffname = chans + 'K1VIS{0}{1}.txt'.format(optic,part)
        ff = Ezff(ffname)
        # copy to other FMs
        fms = []
        if stage=='BF':
            dofs = ['H1','H2','H3','V1','V2','V3','GAS']
        elif stage=='TM':
            dofs = ['SEG1','SEG2','SEG3','SEG4']
        elif stage=='IM':
            dofs = ['H1','H2','H3','V1','V2','V3']
        elif stage=='IP':
            dofs = ['H1','H2','H3']            
        elif stage in ['F0','F1','F2','F3','SF']:
            dofs = ['GAS']            
        else:
            raise ValueError('!')
        
        for dof in dofs:
            switch_on('VIS-{0}_{1}_{2}_{3}'.format(optic,stage,func,dof),mask=mask_wd_ac)
            fmname = '{0}_{1}_{2}_{3}'.format(optic,stage,func,dof)
            print(fmname)
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
                if func not in ['DAMP','IDAMP']:
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
        fname = './filts/{0}_{1}.png'.format(func,stage)
    plt.savefig(fname)
    plt.close()

def show_MAT(optics,stage,func='OSEM2EUL',fname=None,row=6,col=6):
    '''
    '''
    sixsensmat = 'VIS-{o}_{s}_{f}_{c}_{r}'
    chlist = []
    for optic in optics:
        chlist += [[[sixsensmat.format(o=optic,s=stage,f=func,r=r,c=c) for r in range(1,row+1)] for c in range(1,col+1)]]
    data = [read_multi(chnames) for chnames in chlist]
    print(stage,func)
    return data

def switch_on(chname,mask=['INPUT','OFFSET','OUTPUT','DECIMATION']):
    '''
    '''
    FB = ezca.get_LIGOFilter(chname)
    FMs = FB.get_current_swstat_mask().buttons
    FB.only_on(*mask)
    
    
def plot_all():    
    # DAMP
    optics = ['ETMX','ETMY','ITMX','ITMY','BS','SRM','SR2','SR3','PRM','PR2','PR3']
    plot_FILT(optics,'BF',func='DAMP',dofs=['GAS'])
    plot_FILT(optics,'SF',func='DAMP',dofs=['GAS'])
    plot_FILT(optics,'F0',func='DAMP',dofs=['GAS'])
    plot_FILT(optics,'F1',func='DAMP',dofs=['GAS'])
    plot_FILT(optics,'F2',func='DAMP',dofs=['GAS'])
    plot_FILT(optics,'F3',func='DAMP',dofs=['GAS'])        
    plot_FILT(optics,'IM',func='DAMP',dofs=['L','T','V','R','P','Y'])        
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
    plot_FILT(optics,'IP',func='DAMP',dofs=['L','T','Y'])
    plot_FILT(optics,'IP',func='IDAMP',dofs=['L','T','Y'])
    plot_FILT(optics,'IP',func='BLEND',dofs=['LVDTL','LVDTT','LVDTY','ACCL','ACCT','ACCY'])        
    plot_FILT(optics,'IP',func='COILOUTF',dofs=['H1','H2','H3'])        
    # BF damper
    optics = ['ETMX','ETMY','ITMX','ITMY','PRM','PR2','PR3']
    plot_FILT(optics,'BF',func='LVDTINF')
    plot_FILT(optics,'BF',func='COILOUTF')
    plot_FILT(optics,'BF',func='DAMP',dofs=['L','T','V','R','P','Y'])        
    # OSEM
    optics = ['BS','SRM','SR2','SR3','PRM','PR2','PR3']
    plot_FILT(optics,'IM',func='OSEMINF')
    plot_FILT(optics,'IM',func='COILOUTF')
    plot_FILT(optics,'IM',func='DAMP',dofs=['L','T','V','R','P','Y'])
    plot_FILT(optics,'IM',func='OLDAMP',dofs=['L','P','Y'])  
    # PS
    optics = ['ETMX','ETMY','ITMX','ITMY']
    plot_FILT(optics,'IM',func='OSEMINF')
    plot_FILT(optics,'MN',func='OSEMINF')
    plot_FILT(optics,'IM',func='COILOUTF')
    plot_FILT(optics,'MN',func='COILOUTF')
    #plot_FILT(optics,'IM',func='DAMP',dofs=['L','T','V','R','P','Y'])
    plot_FILT(optics,'MN',func='DAMP',dofs=['L','T','V','R','P','Y'])
    plot_FILT(optics,'IM',func='OLDAMP',dofs=['L','P','Y'])        
    # OPLEV
    optics = ['ETMX','ETMY','ITMX','ITMY','BS','SRM','SR2','SR3','PRM','PR2','PR3']
    plot_FILT(optics,'TM',func='OPLEV_TILT',dofs=['SEG1','SEG2','SEG3','SEG4'])
    plot_FILT(optics,'TM',func='OPLEV_LEN',dofs=['SEG1','SEG2','SEG3','SEG4'])
    plot_FILT(optics,'TM',func='COILOUTF',dofs=['H1','H2','H3','H4'])
    plot_FILT(optics,'TM',func='OLDAMP',dofs=['L','P','Y'])                
    optics = ['MCI','MCE','MCO','IMMT1','IMMT2','OSTM','OMMT1','OMMT2']
    plot_FILT(optics,'TM',func='OPLEV_TILT',dofs=['SEG1','SEG2','SEG3','SEG4'])
    plot_FILT(optics,'TM',func='OSEM',dofs=['SEG1','SEG2','SEG3','SEG4'])
    plot_FILT(optics,'TM',func='COILOUTF',dofs=['H1','H2','H3','H4'])
    plot_FILT(optics,'TM',func='OLDAMP',dofs=['L','P','Y'])        
    
if __name__=='__main__':
    #main1()
    #main2()
    #switch_on('VIS-PRM_IM_OSEMINF_V1',mask=['INPUT','OFFSET','FM1','FM9','OUTPUT','DECIMATION','FM8'])
    #copy_param(chname,['PR2','PR3'])

    if True:
        optics = ['MCE','MCI','MCO']
        #optics = all_typea
        init_act(optics,'TM')
    
    if False:
        #optics = ['MCE','MCI','MCO','IMMT1','IMMT2']
        optics = all_optics
        optics.remove('PR3')
        optics.remove('BS')
        optics.remove('SRM')
        optics.remove('SR2')
        optics.remove('SR3')                
        optics.remove('OSTM')
        optics.remove('OMMT1')
        optics.remove('OMMT2')
        print(optics)
        init_oplev(optics,'TM',['OPLEV_TILT','OPLEV_LEN'])
        optics = all_typea
        init_oplev(optics,'PF',['OPLEV_TILT','OPLEV_LEN'])
        init_oplev(optics,'MN',['OPLEV_TILT','OPLEV_LEN','OPLEV_ROL','OPLEV_TRA','OPLEV_VER'])        
    if False:
        optics = ['ITMY','ETMY','ITMX','ETMX']
        mask_wd_ac = ['INPUT','OFFSET','FM1','OUTPUT','DECIMATION']
        init_wd(optics,'IM','WD_OSEMAC_BANDLIM',mask_wd_ac)
        init_wd(optics,'TM','WD_OPLEVAC_BANDLIM_TILT',mask_wd_ac)
        init_wd(optics,'TM','WD_OPLEVAC_BANDLIM_LEN',mask_wd_ac)
        init_wd(optics,'BF','WD_AC_BANDLIM_LVDT',mask_wd_ac)
        init_wd(optics,'IP','WD_AC_BANDLIM_ACC',mask_wd_ac)
        init_wd(optics,'IP','WD_AC_BANDLIM_LVDT',mask_wd_ac)
        init_wd(optics,'F0','WD_AC_BANDLIM',mask_wd_ac)
        init_wd(optics,'F1','WD_AC_BANDLIM',mask_wd_ac)
        init_wd(optics,'F2','WD_AC_BANDLIM',mask_wd_ac)
        init_wd(optics,'F3','WD_AC_BANDLIM',mask_wd_ac)
        init_wd(optics,'SF','WD_AC_BANDLIM',mask_wd_ac)
        pass

    if False:
        #plot_FILT(optics,'IM',fname='before.png')
        #init_OSEMINF(optics,'IM')
        pass    

    if False:
        optics = ['BS','SRM','SR2','SR3','PRM','PR2','PR3']
        optics = ['PRM','PR2','PR3']
        data = show_MAT(optics,'TM',func='OPLEV_TILT_MTRX',row=4,col=4)
        for d,o in zip(data,optics):
            print(o)
            print(d)
        data = show_MAT(optics,'TM',func='OPLEV_LEN_MTRX',row=4,col=4)
        for d,o in zip(data,optics):
            print(o)
            print(d)
        data = show_MAT(optics,'TM',func='OPLEV2EUL',row=4,col=3)
        for d,o in zip(data,optics):
            print(o)
            print(d)
        data = show_MAT(optics,'TM',func='SENSALIGN',row=4,col=3)
        for d,o in zip(data,optics):
            print(o)
            print(d)                                                                                        
        data = show_MAT(optics,'IM',func='OSEM2EUL')
        for d,o in zip(data,optics):
            print(o)
            print(d)
        data = show_MAT(optics,'IM',func='EUL2OSEM')
        for d,o in zip(data,optics):
            print(o)
            print(d)
        data = show_MAT(optics,'IM',func='SENSALIGN')
        for d,o in zip(data,optics):
            print(o)
            print(d)
    if False:
        exit()
        
    if False:
        stages = ['IM']
        optics = ['PRM']
        excs = ['L','T','V','R','P','Y']
        dofs = ['L','T','V','R','P','Y']
        plot(optics,stages,dofs,excs,func='DAMP',prefix='../automeasurement/current/')
