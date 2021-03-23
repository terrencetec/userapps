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
    
    _name = ['K1:VIS-MCO_TM_OPLEV_TILT_SEG1_INMON',
             'K1:VIS-MCO_TM_OPLEV_TILT_SEG2_INMON',
             'K1:VIS-MCO_TM_OPLEV_TILT_SEG3_INMON',
             'K1:VIS-MCO_TM_OPLEV_TILT_SEG4_INMON',
             'K1:VIS-MCO_TM_OPLEV_TILT_PIT_INMON',
             'K1:VIS-MCO_TM_OPLEV_TILT_YAW_INMON',
             'K1:VIS-MCO_TM_OPLEV_TILT_SUM_INMON',
             'K1:VIS-MCO_TM_OPLEV_TILT_CRS_INMON']
    
    col,row = 3,3
    fig, ax = plt.subplots(col,row,figsize=(10,5),sharex=True)
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
    f = open(output,'r',encoding='UTF-8')
    df = f.readlines()
    f.close()
    df = [i.split(',') for i in df]
    df = pd.read_csv(output,header=0)
    df = df.sort_values('Memo')
    
    _name = [#'K1:VIS-MCO_TM_OPLEV_TILT_SEG1_INMON',
             #'K1:VIS-MCO_TM_OPLEV_TILT_SEG2_INMON',
             #'K1:VIS-MCO_TM_OPLEV_TILT_SEG3_INMON',
             #'K1:VIS-MCO_TM_OPLEV_TILT_SEG4_INMON',
             'K1:VIS-MCO_TM_OPLEV_TILT_PIT_INMON',
             'K1:VIS-MCO_TM_OPLEV_TILT_YAW_INMON',
             'K1:VIS-MCO_TM_OPLEV_TILT_SUM_INMON',
             'K1:VIS-MCO_TM_OPLEV_TILT_CRS_INMON']
    
    col,row = 4,1
    fig, ax = plt.subplots(col,row,figsize=(6,8),sharex=True)
    for i,_ax in enumerate(ax):
        if i==3:
            _ax.set_xlabel('Distance [mm]')
        n = i
        
        if n>=len(_name):
            break
        ylabel = 'Value [a.u.]'
        _ax.set_ylabel(ylabel)
        
        if n<len(_name):                
            _ax.errorbar(x=df['Memo'],
                         y=df[_name[n]+'.mean'],
                         yerr=df[_name[n]+'.std'],
                         fmt='ko',label=_name[n],
                         markersize=2,capsize=3)
            #
            _df = df[df['Memo']>4]
            _df = _df[_df['Memo']<11]            
            if 'PIT' in _name[n]:
                func = lambda x,a,b: a+b*x
                x = _df['Memo']
                popt, pcov = curve_fit(func,x,_df[_name[n]+'.mean'])
                _x = np.linspace(int(x.min()),int(x.max())+1,100)
                a,b = popt
                label = '{0:3.2f}*x + {1:3.2f}'.format(b,a)
                _ax.plot(_x,func(_x,*popt),label=label)                
            if 'YAW' in _name[n]:
                func = lambda x,a,b,c,d: a*scipy.special.erf(b*(x-c)) + d
                x = _df['Memo']
                bounds = [[-2, -2, -10, -2],
                          [+2, +2, +10, +2]]
                popt, pcov = curve_fit(func,x,_df[_name[n]+'.mean'],bounds=bounds)
                a,b,c,d = popt                
                _x = np.linspace(int(x.min()),int(x.max())+1,100)
                label = '{0:3.2f}* erf({1:3.2f}(x-{2:3.2f})) + {3:3.2f}'.format(a,b,c,d)
                _ax.plot(_x,func(_x,*popt),label=label)
                func = lambda x,a,b,c: a*b*(x-c)*2/np.sqrt(np.pi)
                label = '{0:3.2f}*(x-{1:3.2f})'.format(a*b*2/np.sqrt(np.pi),c)
                _ax.plot(_x,func(_x,a,b,c),label=label)                
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
                _ax.set_ylim(0,16000)                    
            elif 'CRS' in _name[n]:
                _ax.set_ylim(-5000,5000)
            else:
                _ax.set_ylim(-1.1,1.1)
            _ax.legend(fontsize=7)                
        else:
            break
    #
    
    plt.show()
    plt.savefig('hoge.png')
    plt.close()            
    

if __name__=='__main__':
    #plot('./mco_yaw.txt')
    calibration('./mco_yaw.txt')
