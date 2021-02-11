import numpy as np
from scipy.signal import freqs,freqs_zpk, zpk2tf
import control
import dtt2hdf
from dtt2hdf import read_diaggui,DiagAccess

import matplotlib.pyplot as plt
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

def get_tf(_from,_to):
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

    if stage in ['IM']:
        part = 'payload'
    elif stage in ['BF']:
        part = 'tower'
    else:
        raise ValueError('! {0}'.format(stage))
        
    fname = './current/PLANT_{0}_{3}_{1}_{2}_EXC.xml'.format(optic,test,
                                                             dof_exc,stage)
    # 
    chname_to = 'K1:VIS-{0}_{1}_{2}_{3}_IN1'
    chname_from = 'K1:VIS-{0}_{1}_TEST_{2}_EXC'
    chname_to = chname_to.format(optic2,stage2,func2,dof2)
    chname_from = chname_from.format(optic1,stage1,dof_exc)    
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

def plot_3dofs(optic,stage,func,dofs,exc):
    '''
    '''
    fig,ax = plt.subplots(3,6,figsize=(14,8),sharex=True,sharey='row')
    fig.suptitle('{0} {1} {2} EXC'.format(optic,func,exc))
    plt.subplots_adjust(wspace=0.12,hspace=0.1)
    for i,dof in enumerate(dofs):
        # ------------------------
        if func=='BLEND': # Fix me
            __dof = 'LVDT'+dof
        else:
            __dof = dof
        # ------------------------
        _in = '{0}_{1}_TEST_{2}_EXC'.format(optic,stage,exc)
        _out = '{0}_{1}_{2}_{3}_IN1'.format(optic,stage,func,dof)
        w,tf, coh = get_tf(_in,_out)
        w,hor1, coh = get_tf(_in,_out)
        #_w,tf_fit = get_fitted_tf(w,tf,coh,_in)
        #_w,h = get_fitted_tf(w,hor1,coh,_in)
        idx = np.where(coh>0.0)
        _idx = np.where(coh<0.0)
        if dof==exc:
            style = 'ro'
        else:
            style = 'ko'
        ax[0][i].loglog(w[idx],np.abs(hor1[idx]),style,markersize=1,
                        label='Measured')
        ax[0][i].loglog(w[_idx],np.abs(hor1[_idx]),style,alpha=0.05,
                        markersize=1)
        #ax[0][i].loglog(_w,np.abs(h),'k',label='susmodel')
        ax[0][i].set_ylim(1e-5,5e-1)
        ax[0][i].set_ylim(1e-5,5e1)        
        ax[0][i].set_title('{0} -> {1}'.format(exc,dof))
        ax[1][i].semilogx(w[idx],np.rad2deg(np.angle(hor1[idx]))*-1,
                          style,markersize=1,label='Measured')
        ax[1][i].semilogx(w[_idx],np.rad2deg(np.angle(hor1[_idx]))*-1,
                          style,alpha=0.05,markersize=1)        
        # -1 comes from dtt2hdf's bug???    
        #ax[1][i].semilogx(_w,np.rad2deg(np.angle(h)),'k',label='susmodel')
        ax[1][i].set_ylim(-180,180)
        ax[1][i].set_yticks(range(-180,181,90))
        ax[2][i].semilogx(w[idx],coh[idx],style,markersize=1,label='Measured')
        ax[2][i].semilogx(w[_idx],coh[_idx],style,markersize=1,alpha=0.05)
        ax[2][i].set_ylim(0,1)
        ax[2][i].set_xlim(1e-2,1e1)
        [ax[j][i].grid(which='both',linestyle='dashed') for j in range(3)]
        ax[2][i].legend(loc='lower right')
    [ax[2][i].set_xlabel('Frequency [Hz]') for i in range(6)]
    ax[0][0].set_ylabel('Magnitude\n[um/count, urad/count]')
    ax[1][0].set_ylabel('Phase [Degree]')
    ax[2][0].set_ylabel('Coherence')
    
    #plt.tight_layout()
    if stage in ['IM']:
        part = 'payload'
    elif stage in ['BF']:
        part = 'tower'
    else:
        raise ValueError('!')    
    plt.savefig('./current/PLANT_{0}_{3}_{1}_{2}.png'.format(optic,func,exc,stage,part))
    plt.close()

def plot_3sus(optics,stage,func,dofs,exc):
    '''
    '''
    color = ['k','r','g','m','c','b']
    #
    col = len(dofs)    
    fig,ax = plt.subplots(3,col,figsize=(14,8),sharex=True,sharey='row')
    fig.suptitle('{0} {1} {2} EXC'.format(stage,func,exc))
    plt.subplots_adjust(wspace=0.15,hspace=0.1)
    for j,dof in enumerate(dofs): # j: plot other figure
        for i,optic in enumerate(optics): # i: plot same figure
            _in = '{0}_{1}_TEST_{2}_EXC'.format(optic,stage,exc)
            _out = '{0}_{1}_{2}_{3}_IN1'.format(optic,stage,func,dof)
            w,tf, coh = get_tf(_in,_out)
            idx = np.where(coh>0.1)
            _idx = np.where(coh<0.1)
            style = '{0}o'.format(color[i])
            # Magnitude
            ax[0][j].loglog(w[idx],np.abs(tf[idx]),style,markersize=1,
                            label='Measured ({0})'.format(optic))
            ax[0][j].loglog(w[_idx],np.abs(tf[_idx]),style,alpha=0.05,
                            markersize=1)
            #ax[0][j].set_ylim(1e-5,1e-2)            
            if dof==exc:
                ax[0][j].set_title('{0} -> {1}'.format(exc,dof),color=color[1])
            else:
                ax[0][j].set_title('{0} -> {1}'.format(exc,dof),color=color[0])
            # Phase
            #  * Note: -1 comes from dtt2hdf's bug???
            style = '{0}-'.format(color[i])            
            ax[1][j].semilogx(w[idx],np.rad2deg(np.angle(tf[idx])),#*-1,
                              style,markersize=1,label='Measured ({0})'.format(optic))
            ax[1][j].semilogx(w[_idx],np.rad2deg(np.angle(tf[_idx])),#*-1,
                              style,alpha=0.05,markersize=1)
            ax[1][j].set_ylim(-180,180)
            ax[1][j].set_yticks(range(-180,181,90))
            # Coherence
            ax[2][j].semilogx(w[idx],coh[idx],style,markersize=1,label='Measured ({0})'.format(optic))
            ax[2][j].semilogx(w[_idx],coh[_idx],style,markersize=1,alpha=0.05)
            ax[2][i].set_ylim(0,1)
            ax[2][j].set_xlim(1e-2,20)
    # Setting 
    [ax[i][j].grid(which='both',linestyle='dashed') for j in range(col) for i in range(3)]
    [ax[2][j].legend(loc='lower right',numpoints=1,markerscale=5) for j in range(3)]
    [ax[2][k].set_xlabel('Frequency [Hz]') for k in range(6)]
    ax[0][0].set_ylabel('Magnitude\n[um/count, urad/count]')
    ax[1][0].set_ylabel('Phase [Degree]')
    ax[2][0].set_ylabel('Coherence')
    # Save figure
    plt.tight_layout()
    plt.savefig('./current/PLANT_SUS_{2}_{0}_{1}_EXC.png'.format(func,exc,stage))
    plt.close()


def plot_plant_sus_diag_exc(optics,stage,func,dofs,excs):
    '''
    '''
    color = ['k','r','g','m','c','b']
    #
    col = len(dofs)    
    fig,ax = plt.subplots(3,col,figsize=(14,8),sharex=True,sharey='row')
    fig.suptitle('{0} {1} DIAG EXC'.format(stage,func))
    plt.subplots_adjust(wspace=0.15,hspace=0.1)
    #
    for k,exc in enumerate(excs):
        for j,dof in enumerate(dofs): # j: plot other figure
            if exc==dof:
                print(exc)
                for i,optic in enumerate(optics): # i: plot same figure
                    _in = '{0}_{1}_TEST_{2}_EXC'.format(optic,stage,exc)
                    _out = '{0}_{1}_{2}_{3}_IN1'.format(optic,stage,func,dof)
                    w,tf, coh = get_tf(_in,_out)
                    idx = np.where(coh>0.0)
                    _idx = np.where(coh<0.0)
                    style = '{0}-'.format(color[i])
                    # Magnitude
                    ax[0][j].loglog(w,np.abs(tf),style,markersize=1,linewidth=0.5,
                                    label='Measured ({0})'.format(optic))
                    ax[0][j].set_ylim(1e-6,1e0)
                    ax[0][j].set_title('{0} -> {1}'.format(exc,dof),color=color[0])
                    # Phase
                    style = '{0}o'.format(color[i])                    
                    #  - Note: -1 comes from dtt2hdf's bug???                
                    ax[1][j].semilogx(w,np.rad2deg(np.angle(tf))*-1,style,
                                      markersize=1,label='Measured ({0})'.format(optic))
                    ax[1][j].set_ylim(-180,180)
                    ax[1][j].set_yticks(range(-180,181,90))
                    # Coherence
                    style = '{0}-'.format(color[i])                    
                    ax[2][j].semilogx(w[idx],coh[idx],style,markersize=1,linewidth=0.5,
                                      label='Measured ({0})'.format(optic))
                    ax[2][j].semilogx(w[_idx],coh[_idx],style,markersize=1,alpha=0.05)
                    ax[2][i].set_ylim(0,1)
                    ax[2][j].set_xlim(1e-2,50)
    # Setting 
    [ax[i][j].grid(which='both',linestyle='dashed') for j in range(col) for i in range(3)]
    legs = [ax[2][j].legend(loc='lower right',numpoints=1,markerscale=5) for j in range(len(dofs))]
    [[l.set_linewidth(3) for l in leg.legendHandles] for leg in legs]        
    [ax[2][k].set_xlabel('Frequency [Hz]') for k in range(6)]
    ax[0][0].set_ylabel('Magnitude\n[um/count, urad/count]')
    ax[1][0].set_ylabel('Phase [Degree]')
    ax[2][0].set_ylabel('Coherence')
    # Save figure
    plt.tight_layout()
    plt.savefig('./current/PLANT_SUS_{2}_{0}_DIAG_EXC.png'.format(func,exc,stage))
    plt.close()
    

if __name__=='__main__':
    optics = ['SR2','SRM']
    optics = ['SRM']
    excs = ['L','T','Y']
    excs = ['T']
    dofs = ['L','T','Y']
    funcs = ['IDAMP','BLEND']
    funcs = ['IDAMP']
    from params import params
    for optic in optics:
        for func in funcs:
            for exc in excs:
                plot_3dofs(optic,func,exc)
