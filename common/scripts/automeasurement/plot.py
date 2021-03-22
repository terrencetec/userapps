import numpy as np
from scipy.signal import freqs,freqs_zpk, zpk2tf
#import control
import dtt2hdf
from dtt2hdf import read_diaggui,DiagAccess

import matplotlib.pyplot as plt

color = ['k','r','g','m','c','b']

# ------------------------------------------------------------------------------
def p(w0,Q):
    p1 = -w0/(2*Q)+1j*np.sqrt((w0)**2-w0**2/(4*Q**2))
    p2 = -w0/(2*Q)-1j*np.sqrt((w0)**2-w0**2/(4*Q**2))
    return [p1,p2]

def read_tf(fname,chname_to,chname_from):
    try:
        data = DiagAccess(fname)
        _tf = data.xfer(chname_to,chname_from).xfer
        _coh = data.xfer(chname_to,chname_from).coh
        _omega = data.xfer(chname_to,chname_from).FHz
    except:
        raise ValueError('{0} is invalid file. Please open with diaggui and check the measurement result.'.format(fname))
    return _omega,_tf,_coh

def get_tf(_from,_to,datetime='current',oltf=False):
    '''
    '''
    if not '_EXC' in _from:
        raise ValueError('!')
    if not '_IN1' in _to:
        raise ValueError('!')
    
    optic1,stage1,test,dof_exc = _from.replace('_EXC','').split('_')
    optic2,stage2,func2,dof2,_ = _to.split('_')
    if stage1==stage2:
        stage = stage1
    
    if test!='TEST':
        raise ValueError('!')
    if optic1==optic2:
        optic = optic1
    else:
        raise ValueError('!')

    if datetime=='current':    
        fname = './current/PLANT_{0}_{3}_{1}_{2}_EXC.xml'.format(optic,test,
                                                             dof_exc,stage)
    else:
        fname = './archive/PLANT_{0}_{3}_{1}_{2}_EXC_{4}.xml'.format(optic,test,
                                                                     dof_exc,stage,datetime)
    # 
    chname_to = 'K1:VIS-{0}_{1}_{2}_{3}_IN1'
    chname_from = 'K1:VIS-{0}_{1}_TEST_{2}_EXC'
    chname_to = chname_to.format(optic2,stage2,func2,dof2)
    chname_from = chname_from.format(optic1,stage1,dof_exc)
    if oltf:
        fname = fname.replace('PLANT','OLTF')
        chname_from = chname_from.replace('TEST_{0}_EXC'.format(dof_exc),'DAMP_{0}_IN2'.format(dof_exc))
    return read_tf(fname,chname_to,chname_from)

def blend(lp='high'):
    w0 = 0.5
    f0 = w0/(2.0*np.pi)
    #f0=w0
    if lp=='high':
        num = np.array([1,5*f0**1,10*f0**2,       0,      0,      0])*-1
    else:
        num = np.array([0,      0,       0,10*f0**3,5*f0**4,1*f0**5])
    den =     np.array([1,5*f0**1,10*f0**2,10*f0**3,5*f0**4,1*f0**5])
    blend = control.tf(num,den)
    #control.bode(blend,Plot=True)
    #plt.savefig('hoge.png')
    return blend

def get_fitted_tf(omega_measured,tf_measured,coh_measured,_exc,dof):
    _tf = control.tf(*zpk2tf([],[],0))
    print(_exc,dof)    
    for i in range(5):
        try:
            w0,Q0,k0 = params[_exc][dof][i]
            __tf = control.tf(*zpk2tf([],p(w0,Q0),k0))
            _tf += __tf            
        except:
            pass
            #
    if dof not in _exc:
        _tf = _tf*(blend(lp='low')+blend(lp='high'))
        #_tf = _tf*(blend(lp='low'))
    mag, phase, omega = _tf.freqresp(omega_measured)
    _w = omega
    h = mag*np.exp(1j*phase)#*np.exp(1j*10)
    h = np.squeeze(h)
    return _w,h

def plot_tf(w,tf,coh,ax=None,label='None',style='-',subtitle='No title',**kwargs):
    '''
    '''
    if isinstance(ax,np.ndarray) and len(ax)==3:
        if not subtitle=='':
            ax[0].set_title(subtitle)    
        ax[0].loglog(w,np.abs(tf),style,label=label)
        ax[0].set_ylim(1e-4,100)
        ax[1].semilogx(w,np.rad2deg(np.angle(tf))#*-1, # -1 is come from bug in dtt2hdf
                       ,'o',label=label,markersize=2)
        ax[2].semilogx(w,coh,style,label=label)
        ax[1].set_ylim(-180,180)
        ax[1].set_yticks(range(-180,181,90))
        ax[2].set_ylim(0,1)
        ax[2].set_xlim(1e-2,100)
        leg = ax[0].legend(loc='lower left',numpoints=1,markerscale=5)
        [l.set_linewidth(3) for l in leg.legendHandles]
    elif not isinstance(ax,list):
        ax.loglog(w,np.abs(tf),style,label=label,**kwargs)
        ax.set_ylim(1e-6,100)
        ax.set_xlim(1e-2,100)
        leg = ax.legend(numpoints=1,markerscale=5)
    
def plot_couple(optics,stages,dofs,excs,func='DAMP',datetime='current'):
    '''
    '''
    stage = stages[0]
    optic = optics[0]
    for optic in optics:
        for dof in dofs:
            fig,ax = plt.subplots(1,1,figsize=(5,5),sharex=True,sharey='row')
            fig.suptitle('Coupling TFs to {0}_{1}_{2}_{3}'.format(optic,stage,func, dof))
            for i,exc in enumerate(excs): # i: plot same figure
                # get_data
                _in = '{0}_{1}_TEST_{2}_EXC'.format(optic,stage,exc)
                _out = '{0}_{1}_{2}_{3}_IN1'.format(optic,stage,func,dof)
                w, tf, coh = get_tf(_in,_out,datetime=datetime)
                # plot
                label = '{0}{1} -> {0}{2}'.format(stage,exc,dof)
                title = ''
                if exc==dof:
                    plot_tf(w,tf,coh,ax,label=label,subtitle=title,linewidth=3,zorder=0)
                else:
                    plot_tf(w,tf,coh,ax,label=label,subtitle=title,alpha=0.5)

            if datetime=='current':    
                fname = './current/PLANT_{0}_{1}_{2}_{3}_COUPLE.png'.format(optic,stage,func,dof)
            else:
                fname = './archive/PLANT_{0}_{1}_{2}_{3}_COUPLE_{4}.png'.format(optic,stage,func,dof,datetime)
            
            print(fname)
            ax.set_xlabel('Frequency [Hz]')
            if dof in ['L','T','V','GAS']:
                ax.set_ylabel('Magnitude [um/count]')
            elif dof in ['R','P','Y']:
                ax.set_ylabel('Magnitude [urad/count]')
            else:
                raise ValueError('!')
            
            plt.tight_layout()
            plt.savefig(fname)
            plt.close()
        

def plot(optics,stages,dofs,excs,func='DAMP',datetime='current',oltf=False):
    '''
    '''
    fig,ax = plt.subplots(3,6,figsize=(14,8),sharex=True,sharey='row')
    #
    if excs==dofs and len(stages)==1:
        stage = stages[0]
        fig.suptitle('{0} {1} DIAG EXC'.format(stage,func))
        for j,dof in enumerate(dofs): # j: plot other figure
            for i,optic in enumerate(optics): # i: plot same figure
                exc = dof
                # get_data
                _in = '{0}_{1}_TEST_{2}_EXC'.format(optic,stage,exc)
                _out = '{0}_{1}_{2}_{3}_IN1'.format(optic,stage,func,dof)
                w, tf, coh = get_tf(_in,_out,datetime=datetime,oltf=oltf)            
                # plot
                label = '{0}'.format(optic)
                title = '{0}->{1}'.format(exc,dof)
                plot_tf(w,tf,coh,ax[:,j],label=label,subtitle=title,oltf=oltf)
        if datetime=='current':
            fname = './current/OLTF_SUS_{1}_{2}_DIAG_EXC.png'.format(optic,stage,func,exc)
        else:
            fname = './archive/OLTF_SUS_{1}_{2}_DIAG_EXC_{4}.png'.format(optic,stage,func,exc,datetime)
    else:
        raise ValueError('!')    
    print(fname)
    [ax[2][k].set_xlabel('Frequency [Hz]') for k in range(6)]
    ax[0][0].set_ylabel('Magnitude\n[um/count, urad/count]')
    ax[1][0].set_ylabel('Phase [Degree]')
    ax[2][0].set_ylabel('Coherence')    
    plt.tight_layout()
    plt.savefig(fname)
    plt.close()        

        
def plot_diag(optics,stages,dofs,excs,func='DAMP',datetime='current',oltf=False):
    ''' Plot 
    
    Parameters
    ----------
    optics: list of `str`
        optics name.
    stages: list of `str`
        stage name.
    dofs: list of `str`
        dofs name    
    excs: list of `str`
        excs name
    func: `str`
        function name.
    prefix: `str`
        prefix        
    '''
    if len(dofs)<3:
        num = 3
    else:
        num = 6
    fig,ax = plt.subplots(3,num,figsize=(14,8),sharex=True,sharey='row')
    #
    if len(dofs)*len(excs)==1:  # for GAS
        dof,exc = dofs[0],excs[0]
        fig.suptitle('{0} {1} EXC'.format(func,exc))        
        for j,stage in enumerate(stages): # j: plot other figure
            for i,optic in enumerate(optics): # i: plot same figure
                # get_data
                _in = '{0}_{1}_TEST_{2}_EXC'.format(optic,stage,exc)
                _out = '{0}_{1}_{2}_{3}_IN1'.format(optic,stage,func,dof)
                w, tf, coh = get_tf(_in,_out,datetime=datetime)
                # plot
                label = '{0}'.format(optic)
                title = '{0}->{0}'.format(stage)
                plot_tf(w,tf,coh,ax[:,j],label=label,subtitle=title)        
        fname = prefix+'PLANT_SUS_GAS_DIAG_EXC.png'
    elif len(stages)*len(excs)==1:
        stage,exc = stages[0],excs[0]
        fig.suptitle('{0} {1} {2} EXC'.format(stage,func,exc))                
        for j,dof in enumerate(dofs): # j: plot other figure
            for i,optic in enumerate(optics): # i: plot same figure
                # get_data
                _in = '{0}_{1}_TEST_{2}_EXC'.format(optic,stage,exc)
                _out = '{0}_{1}_{2}_{3}_IN1'.format(optic,stage,func,dof)
                w, tf, coh = get_tf(_in,_out,datetime=datetime)            
                # plot
                label = '{0}'.format(optic)
                title = '{0}->{1}'.format(exc,dof)
                plot_tf(w,tf,coh,ax[:,j],label=label,subtitle=title)                
        fname = prefix+'PLANT_SUS_{1}_{2}_{3}_EXC.png'.format(optic,stage,func,exc)
    elif excs==dofs and len(stages)==1:
        stage = stages[0]
        fig.suptitle('{0} {1} DIAG EXC'.format(stage,func))
        for j,dof in enumerate(dofs): # j: plot other figure
            for i,optic in enumerate(optics): # i: plot same figure
                exc = dof
                # get_data
                _in = '{0}_{1}_TEST_{2}_EXC'.format(optic,stage,exc)
                _out = '{0}_{1}_{2}_{3}_IN1'.format(optic,stage,func,dof)
                w, tf, coh = get_tf(_in,_out,datetime=datetime)            
                # plot
                label = '{0}'.format(optic)
                title = '{0}->{1}'.format(exc,dof)
                plot_tf(w,tf,coh,ax[:,j],label=label,subtitle=title)
        if datetime=='current':
            fname = './current/PLANT_SUS_{1}_{2}_DIAG_EXC.png'.format(optic,stage,func,exc)
        else:
            fname = './archive/PLANT_SUS_{1}_{2}_DIAG_EXC_{4}.png'.format(optic,stage,func,exc,datetime)            
    else:
        raise ValueError('!')    
    print(fname)
    [ax[2][k].set_xlabel('Frequency [Hz]') for k in range(num)]
    ax[0][0].set_ylabel('Magnitude\n[um/count, urad/count]')
    ax[1][0].set_ylabel('Phase [Degree]')
    ax[2][0].set_ylabel('Coherence')    
    plt.tight_layout()
    plt.savefig(fname)
    plt.close()
    
if __name__=='__main__':
    optics = ['PRM']
    stages = ['IM']
    excs = ['L','T','V','R','P','Y']
    dofs = ['L','T','V','R','P','Y']    
    plot_diag(optics,stages,dofs,excs,func='DAMP',datetime='current')
    
    optics = ['PRM']
    stages = ['IM']    
    excs = ['L','T','V','R','P','Y']
    dofs = ['L','T','V','R','P','Y']    
    plot_couple(optics,stages,dofs,excs,func='DAMP',datetime='current')    
    exit()
    
    stages = ['SF','BF']
    optics = ['PRM','PR2','PR3']
    excs = ['GAS']
    dofs = ['GAS']
    plot_diag(optics,stages,dofs,excs,func='DAMP')

    stages = ['BF']
    optics = ['PRM','PR2','PR3']    
    excs = ['L']
    dofs = ['L','T','V']
    plot_diag(optics,stages,dofs,excs,func='DAMP')
    
    stages = ['BF']
    optics = ['PRM','PR2','PR3']
    excs = ['L','T','V']
    dofs = ['L','T','V']
    plot_diag(optics,stages,dofs,excs,func='DAMP')
    
