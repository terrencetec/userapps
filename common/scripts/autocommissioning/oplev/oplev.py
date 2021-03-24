#!/usr/bin/env python3
#! coding:utf-8
from cdsutils import avg
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.optimize import curve_fit
import scipy

def plot(output):
    f = open(output,'r',encoding='UTF-8')
    df = f.readlines()
    f.close()
    df = [i.split(',') for i in df]
    df = pd.read_csv(output,header=0)
    
    _name = ['K1:VIS-MCE_TM_OPLEV_TILT_SEG1_INMON',
             'K1:VIS-MCE_TM_OPLEV_TILT_SEG2_INMON',
             'K1:VIS-MCE_TM_OPLEV_TILT_SEG3_INMON',
             'K1:VIS-MCE_TM_OPLEV_TILT_SEG4_INMON',
             'K1:VIS-MCE_TM_OPLEV_TILT_PIT_INMON',
             'K1:VIS-MCE_TM_OPLEV_TILT_YAW_INMON',
             'K1:VIS-MCE_TM_OPLEV_TILT_SUM_INMON',
             'K1:VIS-MCE_TM_OPLEV_TILT_CRS_INMON']
    
    col,row = 3,3
    fig, ax = plt.subplots(col,row,figsize=(10,4),sharex=True)
    for i,ax_col in enumerate(ax):
        for j,_ax in enumerate(ax_col):
            if i==col-1:
                _ax.set_xlabel('Distance [mm]')
            n = i*col+j

            if n>=len(_name):
                break
            # if 'INMON' in _name[n]:
            #     ylabel = 'Value [count]'
            # elif 'OUT':
            #     ylabel = 'Value [mm]'
            ylabel = 'Value [a.u.]'
            _ax.set_ylabel(ylabel)
            
            if n<len(_name):                
                _ax.errorbar(x=df['Memo'],
                             y=df[_name[n]+'.mean'],
                             yerr=df[_name[n]+'.std'],
                             fmt='ko',label=_name[n],
                             markersize=2,capsize=3)
                _ax.legend(fontsize=7)
                if 'SEG' in _name[n]:
                    _ax.set_ylim(-10000,0)
                elif 'SUM' in _name[n]:
                    _ax.set_ylim(0,16000)                    
                elif 'CRS' in _name[n]:
                    _ax.set_ylim(-5000,5000)
                else:
                    _ax.set_ylim(-1,1)
            else:
                break
    #plt.show()
    plt.savefig('hoge.png')
    plt.close()    

def calibration(output):
    '''
    '''
    optic, dof = output.replace('.txt','').split('_')
    optic = optic.upper()
    dof = dof.upper()
    print(optic,dof)
    f = open(output,'r',encoding='UTF-8')
    df = f.readlines()
    f.close()
    df = [i.split(',') for i in df]
    df = pd.read_csv(output,header=0)
    df = df.sort_values('Memo')
    
    _name = ['K1:VIS-{0}_TM_OPLEV_TILT_PIT_INMON'.format(optic),
             'K1:VIS-{0}_TM_OPLEV_TILT_YAW_INMON'.format(optic),
             'K1:VIS-{0}_TM_OPLEV_TILT_SUM_INMON'.format(optic),
             'K1:VIS-{0}_TM_OPLEV_TILT_CRS_INMON'.format(optic)]
    
    col,row = 4,1
    fig, ax = plt.subplots(col,row,figsize=(8,8),sharex=True)
    fig.subplots_adjust(wspace=0.1, hspace=0.05, left=0.15, right=0.6, top=0.92)
    plt.suptitle('OpLev calibration of {0} {1}'.format(optic,dof),fontsize=20)
    for i,_ax in enumerate(ax):
        if i==3:
            _ax.set_xlabel('Distance [mm]')
        n = i
        
        if n>=len(_name):
            break
        ylabel = 'Value [count]'
        _ax.set_ylabel(ylabel)
        
        if n<len(_name):
            _ax.errorbar(x=df['Memo'],
                         y=df[_name[n]+'.mean'],
                         yerr=df[_name[n]+'.std'],
                         fmt='ko',label=_name[n],
                         markersize=2,capsize=3)
            #
            _df = df[df['Memo']>=df['Memo'].min()+1]
            _df = _df[_df['Memo']<=_df['Memo'].max()-1.5]
            if dof not in _name[n]:
                if 'SUM' not in _name[n] and 'CRS' not in _name[n]:
                    func = lambda x,a,b: a+b*x
                    x = _df['Memo']
                    popt, pcov = curve_fit(func,x,_df[_name[n]+'.mean'])
                    _x = np.linspace(int(x.min()),int(x.max())+1,100)
                    a,b = popt
                    label = '{0:3.2f}*x + {1:3.2f}'.format(b,a)
                    _ax.plot(_x,func(_x,*popt),label=label)
            if dof in _name[n]:
                func = lambda x,a,b,c,d: a*scipy.special.erf(b*(x-c)) + d
                x = _df['Memo']
                bounds = [[-1, -5, -20, -2],
                          [+1, +5, +20, +2]]
                popt, pcov = curve_fit(func,x,_df[_name[n]+'.mean'],bounds=bounds)
                a,b,c,d = popt
                _x = np.linspace(int(x.min()),int(x.max())+1,100)
                label = '{0:3.2f}* erf({1:3.2f}(x-{2:3.2f})) + {3:3.2f}'.format(a,b,c,d)
                _ax.plot(_x,func(_x,*popt),label=label)
                func = lambda x,a,b,c: a*b*(x-c)*2/np.sqrt(np.pi)
                slope_inv = a*b*2/np.sqrt(np.pi)
                label = '{0:3.2f}*(x-{1:3.2f})'.format(slope_inv,c)
                _ax.plot(_x,func(_x,a,b,c),label=label)

                sigma = 1/b*np.sqrt(2)
                linrange = sigma/2 #?
                print('Beam radius is {0:3.2f} [mm]?.'.format(sigma))
                print('Linear range is {0:3.2f} [mm]?.'.format(linrange))                
                _ax.vlines(x=c,ymin=-1,ymax=1,color='black',linestyle='--')                
                _ax.axvspan(c-linrange,c+linrange,color='gray',alpha=0.3)
                
            if 'SUM' in _name[n]:
                func = lambda x,a,b: a+b*x
                x = _df['Memo']
                popt, pcov = curve_fit(func,x,_df[_name[n]+'.mean'])
                _x = np.linspace(int(x.min()),int(x.max())+1,100)            
                a,b = popt
                label = '{0:3.2f}*x + {1:3.2f}'.format(b,a)
                _ax.plot(_x,func(_x,*popt),label=label)   
                
            if 'SEG' in _name[n]:
                _ax.set_ylim(-10000,0)
            elif 'SUM' in _name[n]:
                _ax.set_ylim(0,20000)                    
            elif 'CRS' in _name[n]:
                _ax.set_ylim(-5000,5000)
            else:
                _ax.set_ylim(-1.1,1.1)
            _ax.legend(fontsize=8,loc='upper left',bbox_to_anchor=(1, 1))
            _ax.grid(which='major',color='gray',linestyle='--')
        else:
            break
    #
    if True:
        plt.show()
    else:
        fname = output.replace('.txt','.png')
        plt.savefig(fname)
    plt.close()            
    
if __name__=='__main__':
    #plot('./mco_yaw.txt')
    calibration('mco_yaw.txt')    
    calibration('mce_yaw.txt')
    calibration('mce_pit.txt')
