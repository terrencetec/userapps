import numpy as np
import matplotlib.pyplot as plt
from gwpy.time import tconvert
from gwpy.timeseries import TimeSeriesDict

kwargs = {'host':'10.68.10.121',
          'port':8088,
          'verbose':True,
          'start':tconvert('Dec 16 18:00:00 2020 JST'),
          'end':tconvert('Dec 17 06:00:00 2020 JST')
}

chname = ['K1:VIS-SRM_IP_LVDTINF_H1_OUT16',
          'K1:VIS-SRM_IP_LVDTINF_H2_OUT16',
          'K1:VIS-SRM_IP_LVDTINF_H3_OUT16']

data = TimeSeriesDict.fetch(chname,**kwargs)


if __name__=='__main__':
    fftlen = 2**9
    overlap = fftlen/2
    
    chname = ['K1:VIS-SRM_IP_LVDTINF_H1_OUT16',
              'K1:VIS-SRM_IP_LVDTINF_H2_OUT16',
              'K1:VIS-SRM_IP_LVDTINF_H3_OUT16']
    labels = ['H1','H2','H3']

    fig,ax = plt.subplots(2,2,figsize=(10,6))
    fig.suptitle('No title')
    plt.subplots_adjust(wspace=0.1,hspace=0.1)
    
    alpha=1.0
    h1 = data['K1:VIS-SRM_IP_LVDTINF_H1_OUT16']
    h2 = data['K1:VIS-SRM_IP_LVDTINF_H2_OUT16']
    h3 = data['K1:VIS-SRM_IP_LVDTINF_H3_OUT16']
    h = [h1,h2,h3]
    h1 = h1.asd(fftlength=fftlen,overlap=overlap)
    h2 = h2.asd(fftlength=fftlen,overlap=overlap)
    h3 = h3.asd(fftlength=fftlen,overlap=overlap)    
    mat0 = np.array([[0.61185,-0.5339,-0.00848],
                    [0.25410,0.39689,-0.6673],
                    [0.54257,0.53505,0.59110]])
    print(mat0)
    _l = h[0]*mat0[0][0] + h[1]*mat0[0][1] + h[2]*mat0[0][2]
    _t = h[0]*mat0[1][0] + h[1]*mat0[1][1] + h[2]*mat0[1][2]
    _y = h[0]*mat0[2][0] + h[1]*mat0[2][1] + h[2]*mat0[2][2]
    
    def poyo(l,t,y):
        coh_lt = l.csd(t,fftlen,overlap).abs()
        coh_ly = l.csd(y,fftlen,overlap).abs()
        coh_ty = t.csd(y,fftlen,overlap).abs()
        coh_tl = 1/coh_lt
        coh_yl = 1/coh_ly
        coh_yt = 1/coh_ty
        coh = [[1,coh_lt,coh_ly],
               [coh_tl,1,coh_ty],
               [coh_yt,coh_yl,1]]
        return coh
    coh0 = poyo(_l,_t,_y)
    _l = _l.asd(fftlength=fftlen,overlap=overlap)
    _t = _t.asd(fftlength=fftlen,overlap=overlap)
    _y = _y.asd(fftlength=fftlen,overlap=overlap)

    #
    def x(coh):
        return np.mean(coh.crop(0.04,0.06),axis=0).value
    _coh0 = [[1,        x(coh0[0][1]),x(coh0[0][2])],
            [x(coh0[1][0]),1,        x(coh0[1][2])],
            [x(coh0[2][0]),x(coh0[2][1]),1        ]]
    w,v = np.linalg.eig(_coh0)
    print(v)
    a1,a2,a3,R = np.deg2rad(22), np.deg2rad(142), np.deg2rad(262), 0.579 
    mat = np.array([[np.cos(a1), np.sin(a1), R],
                    [np.cos(a2), np.sin(a2), R],
                    [np.cos(a3), np.sin(a3), R]])
    mat = np.linalg.inv(mat)
    theta = np.deg2rad(0)
    align = np.array([[np.cos(theta),-1*np.sin(theta),0],
                      [np.sin(theta),np.cos(theta),0],
                      [0,0,1]])
    # --------------------------------------------------
    #mat = np.dot(v.T,mat)    
    print(mat)
    l = h[0]*mat[0][0] + h[1]*mat[0][1] + h[2]*mat[0][2]
    t = h[0]*mat[1][0] + h[1]*mat[1][1] + h[2]*mat[1][2]
    y = h[0]*mat[2][0] + h[1]*mat[2][1] + h[2]*mat[2][2]
    h = [l,t,y]
    mat = np.array([[1,-0.1,0],
                    [0.1,1,0],
                    [0,0,1]])    
    l = h[0]*mat[0][0] + h[1]*mat[0][1] + h[2]*mat[0][2]
    t = h[0]*mat[1][0] + h[1]*mat[1][1] + h[2]*mat[1][2]
    y = h[0]*mat[2][0] + h[1]*mat[2][1] + h[2]*mat[2][2]    
    coh = poyo(l,t,y)
    # -------------------------------------------------
    l = l.asd(fftlength=fftlen,overlap=overlap)
    t = t.asd(fftlength=fftlen,overlap=overlap)
    y = y.asd(fftlength=fftlen,overlap=overlap)
    
    #[ax[0].loglog(,label=labels[i]) for i in range(3)]
    ax[0][0].loglog(l,label='l')
    ax[0][0].loglog(t,label='t')
    ax[0][0].loglog(y,label='y')
    ax[0][1].loglog(_l,label='l')
    ax[0][1].loglog(_t,label='t')
    ax[0][1].loglog(_y,label='y')
    #ax[0][1].plot(h1,label='l')
    #ax[0][1].plot(h2,label='t')
    #ax[0][1].plot(h3,label='y')    
    ax[1][0].plot(coh[0][1],label='l/t')
    ax[1][0].plot(coh[0][2],label='l/y')
    ax[1][0].plot(coh[1][2],label='t/y')
    ax[1][1].plot(coh0[0][1],label='l/t')
    ax[1][1].plot(coh0[0][2],label='l/y')
    ax[1][1].plot(coh0[1][2],label='t/y')    
    ax[0][0].legend()
    ax[1][0].legend()
    ax[1][0].set_xlim(1e-2,0.1)
    ax[1][1].set_xlim(1e-2,0.1)
    #ax[0][1].set_ylim(1e0,2e1)
    #ax[0][1].set_xlim(3e-1,3.2e-1)    
    plt.savefig('hoge.png')
    plt.close()    
