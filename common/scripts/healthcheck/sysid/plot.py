import numpy as np
from scipy.signal import freqs_zpk
import dtt2hdf
from dtt2hdf import read_diaggui,DiagAccess

import matplotlib.pyplot as plt

def hoge(exc,seg):
    fname = './measurements/OSTM_TM_{0}_EXC.xml'.format(exc)
    data = DiagAccess(fname)
    seg1 = data.xfer('K1:VIS-OSTM_TM_OPLEV_SEG1_IN1_DQ','K1:VIS-OSTM_TM_COILOUTF_{0}_EXC'.format(exc)).xfer
    seg2 = data.xfer('K1:VIS-OSTM_TM_OPLEV_SEG2_IN1_DQ','K1:VIS-OSTM_TM_COILOUTF_{0}_EXC'.format(exc)).xfer
    seg3 = data.xfer('K1:VIS-OSTM_TM_OPLEV_SEG3_IN1_DQ','K1:VIS-OSTM_TM_COILOUTF_{0}_EXC'.format(exc)).xfer
    seg4 = data.xfer('K1:VIS-OSTM_TM_OPLEV_SEG4_IN1_DQ','K1:VIS-OSTM_TM_COILOUTF_{0}_EXC'.format(exc)).xfer
    w = data.xfer('K1:VIS-OSTM_TM_OPLEV_SEG1_IN1_DQ','K1:VIS-OSTM_TM_COILOUTF_{0}_EXC'.format(exc)).FHz
    #
    def p(w0,Q):
        p1 = -w0/(2*Q)+1j*np.sqrt((w0)**2-w0**2/(4*Q**2))
        p2 = -w0/(2*Q)-1j*np.sqrt((w0)**2-w0**2/(4*Q**2))
        return [p1,p2]

    # for H1_EXC
    if seg=='SEG1':
        w0,Q0,k0 = 1.25 ,3  , 2.5e-2 # Len
        w1,Q1,k1 = 3.4  ,5  , 5.3e-2 #
        w2,Q2,k2 = 5.3  ,7  , 4.2e-2 # Len
        w3,Q3,k3 =  9   ,20 , 1.0e-3 #
        w4,Q4,k4 = 15   ,20 , 3.0e-3 #
        w5,Q5,k5 = 17   ,20 , 2.0e-2 # 
    elif seg=='SEG2':
        w0,Q0,k0 = 1.25 ,3  , 2.5e-2
        w1,Q1,k1 = 3.4  ,5  , 1.5e-2
        w2,Q2,k2 = 5.3  ,7  , 2.0e-2
        w3,Q3,k3 =  9   ,20 , 2.0e-3 #
        w4,Q4,k4 = 15   ,20 , 1.0e-3 #
        w5,Q5,k5 = 17   ,20 ,-1.0e-3 #         
    elif seg=='SEG3':
        w0,Q0,k0 = 1.25 ,3  , 2.5e-2
        w1,Q1,k1 = 3.4  ,5  ,-1.5e-3
        w2,Q2,k2 = 5.3  ,7  , 1.5e-2
        w3,Q3,k3 =  9   ,20 ,-1.0e-4 #
        w4,Q4,k4 = 15   ,20 , 1.0e-4 #
        w5,Q5,k5 = 17   ,20 ,-7.0e-3 #
    elif seg=='SEG4':
        w0,Q0,k0 = 1.25 ,3  , 3.0e-3 # Len
        w1,Q1,k1 = 3.4  ,5  , 1.5e-2 #
        w2,Q2,k2 = 5.3  ,7  , 3.5e-2 # Len
        w3,Q3,k3 =  9   ,20 ,-3.0e-3 #
        w4,Q4,k4 = 15   ,20 , 3.5e-3 #
        w5,Q5,k5 = 17   ,20 ,-4.5e-3 #
    else:
        pass
    
    _w1,h1 = freqs_zpk([],p(w0,Q0),k0,w)
    _w2,h2 = freqs_zpk([],p(w1,Q1),k1,w)
    _w3,h3 = freqs_zpk([],p(w2,Q2),k2,w)
    _w4,h4 = freqs_zpk([],p(w3,Q3),k3,w)
    _w5,h5 = freqs_zpk([],p(w4,Q4),k4,w)
    _w6,h6 = freqs_zpk([],p(w5,Q5),k5,w)

    # unknown Delay
    if seg=='SEG3':
        #_w1,delay = freqs_zpk([-0.46],[-12.3],7,w) # de-white
        _w1,delay = freqs_zpk([-0.5],[-5],-8,w) # de-white and minus sign caused from dtt2hdf
    else:
        #_w1,delay = freqs_zpk([-0.46],[-12.3],7,w) # de-white        
        _w1,delay = freqs_zpk([-0.5],[-5],8,w) # de-white               
    
    _w,h = _w1,(h1+h2+h3+h4+h5+h6)*delay
    
    if seg=='SEG1':
        seg1 = seg1
        coh = data.xfer('K1:VIS-OSTM_TM_OPLEV_SEG1_IN1_DQ','K1:VIS-OSTM_TM_COILOUTF_{0}_EXC'.format(exc)).coh    
    elif seg=='SEG2':
        seg1 = seg2
        coh = data.xfer('K1:VIS-OSTM_TM_OPLEV_SEG2_IN1_DQ','K1:VIS-OSTM_TM_COILOUTF_{0}_EXC'.format(exc)).coh    
    elif seg=='SEG3':
        seg1 = seg3
        coh = data.xfer('K1:VIS-OSTM_TM_OPLEV_SEG3_IN1_DQ','K1:VIS-OSTM_TM_COILOUTF_{0}_EXC'.format(exc)).coh        
    elif seg=='SEG4':
        seg1 = seg4
        coh = data.xfer('K1:VIS-OSTM_TM_OPLEV_SEG4_IN1_DQ','K1:VIS-OSTM_TM_COILOUTF_{0}_EXC'.format(exc)).coh            
    else:
        pass

    return w,seg1,w1,_w1,h1,_w2,h2,_w3,h3,_w4,h4,_w5,h5,_w6,h6,_w,h,coh
    
if __name__=='__main__':
    exc = 'H1'
    seg = 'SEG2'
    segs = ['SEG1','SEG2','SEG3','SEG4']
    fig,ax = plt.subplots(3,4,figsize=(16,6),sharex=True)
    for i,seg in enumerate(segs):
        w,seg1,w1,_w1,h1,_w2,h2,_w3,h3,_w4,h4,_w5,h5,_w6,h6,_w,h,coh = hoge(exc,seg)    
        ax[0][i].loglog(w,np.abs(seg1),'ro',markersize=1)
        ax[0][i].loglog(_w1,np.abs(h1),'k--',alpha=0.4)
        ax[0][i].loglog(_w2,np.abs(h2),'k--',alpha=0.4)
        ax[0][i].loglog(_w3,np.abs(h3),'k--',alpha=0.4)
        ax[0][i].loglog(_w4,np.abs(h4),'k--',alpha=0.4)
        ax[0][i].loglog(_w5,np.abs(h5),'k--',alpha=0.4)
        ax[0][i].loglog(_w6,np.abs(h6),'k--',alpha=0.4)
        ax[0][i].loglog(_w,np.abs(h),'k')
        ax[0][i].set_ylim(1e-5,2e-1)
        ax[1][i].semilogx(w,np.rad2deg(np.angle(seg1))*-1,'ro',markersize=1) # -1 comes from dtt2hdf's bug???    
        ax[1][i].semilogx(_w,np.rad2deg(np.angle(h)),'k')
        ax[1][i].set_ylim(-180,180)        
        ax[2][i].semilogx(w,coh,'ro',markersize=1)
        ax[2][i].set_ylim(0,1)
    plt.tight_layout()
    plt.savefig('h3_exc.png')
    plt.close()
            
