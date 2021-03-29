#!/home/controls/miniconda3/envs/miyoconda37/bin/python 
#! coding:utf-8

import os
from cdsutils import avg
from ezca import ezca
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

chname = []
plotnum = []

def plot(chname,fname):
    '''
    '''
    df = pd.read_csv(fname,header=0)
    col,row = 3,3
    fig, ax = plt.subplots(col,row,figsize=(10,5),sharex=True)
    for i,ax_col in enumerate(ax):
        for j,_ax in enumerate(ax_col):
            if i==col-1:
                _ax.set_xlabel('Distance [um]')
            n = i*col+j

            if n>=len(chname):
                break
            ylabel = 'Value [a.u.]'
            _ax.set_ylabel(ylabel)
            
            if n<len(chname):           
                _ax.errorbar(x=df['Disp'],
                             y=df[chname[n]+'.mean'],
                             yerr=df[chname[n]+'.std'],
                             fmt='ko',label=chname[n],
                             markersize=2,capsize=3)
                _ax.legend(fontsize=7)
                if 'SEG' in chname[n]:
                    _ax.set_ylim(-10000,0)
                elif 'SUM' in chname[n]:
                    _ax.set_ylim(0,20000)
                elif 'CRS' in chname[n]:
                    _ax.set_ylim(-5000,5000)
                else:
                    _ax.set_ylim(-1,1)
            else:
                break
    plt.show()
    plt.savefig('hoge.png')
    plt.close()
    
def init(channellist):
    '''
    '''
    with open(channellist,'r',encoding='UTF-8') as f: 
        chname = f.read().splitlines()
        chname = [name for name in chname if name[0]!='#']
    return chname

def getdata(chname):
    '''
    '''
    now = datetime.now()
    _avg = np.array(avg(1,chname,stddev=True))
    data = [[str(now),disp,*list(map(lambda x:'{0:.3f}'.format(x),_avg.flatten()))]]
    return data
    
def add(chname,fname):
    '''
    '''
    data = getdata(chname)
    txt = ','.join(data[0])+'\n'        
    with open(fname,'a') as f:
        f.write(txt)

def init(chname,fname):
    '''
    '''
    data = getdata(chname)                
    name = np.array([[ch+'.mean',ch+'.std'] for ch in chname]).flatten()
    txt = 'DateTime,Disp,'+','.join(name)+'\n'
    with open(fname,'w') as f:
        f.write(txt)
        

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description='hoge')
    parser.add_argument('--plot',action='store_true')    
    parser.add_argument('--init',action='store_true')
    parser.add_argument('-o','--optic',default='MCE')
    parser.add_argument('-f','--func',default='OPLEV_TILT')
    parser.add_argument('-d','--dof',default='YAW')    
    args = parser.parse_args()
    optic = args.optic.upper()
    func = args.func.upper()
    dof = args.dof.upper()
    ezca = ezca.Ezca()
    disp = ezca['VIS-{0}_INSTALLED_DATE'.format(optic)]
    print(disp)
    dofs = ['SEG1','SEG2','SEG3','SEG4','PIT','YAW','SUM','CRS']
    chname = []
    for dof in dofs:
        chname +=['K1:VIS-{0}_TM_{1}_{2}_INMON'.format(optic,func,dof)]
        
    fname = '/opt/rtcds/userapps/release/vis/common/scripts/autocommissioning/oplev/{0}_{1}.txt'.format(optic.lower(),dof.lower())
    
    if args.plot:
        plot(chname,fname)
        exit()

    if args.init:
        init(chname,fname)
        
    if os.path.exists(fname):
        add(chname,fname)
        plot(chname,fname)                
    else:
        init(chname,fname)
        add(chname,fname)        
        plot(chname,fname)        
