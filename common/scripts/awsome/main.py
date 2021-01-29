#!/usr/bin/env python3
#! coding:utf-8
from cdsutils import avg
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

chname = []
plotnum = []
screw_pitch = 1.0 * 1000.0

def plot(output):
    f = open(output,'r',encoding='UTF-8')
    df = f.readlines()
    f.close()
    df = [i.split(',') for i in df]

    df = pd.read_csv(output,header=0)

    idx = [2,4,6,38,12,54,16,18,20]
    
    _name = ['K1:VIS-PR2_BF_LVDTINF_H1_INMON',
             'K1:VIS-PR2_BF_LVDTINF_V1_INMON',
             'K1:VIS-PR2_BF_LVDTINF_H1_INMON',
             'K1:VIS-PR2_BF_LVDTINF_H2_INMON']
    
    col,row = 2,2
    fig, ax = plt.subplots(col,row,figsize=(10,4),sharex=True)
    for i,ax_col in enumerate(ax):
        for j,_ax in enumerate(ax_col):
            if i==col-1:
                _ax.set_xlabel('Calibrated stepper distance [um]')                
            n = i*2+j

            if 'INMON' in _name[n]:
                ylabel = 'Value [count]'
            elif 'OUT':
                ylabel = 'Value [um]'                
            _ax.set_ylabel(ylabel)
            
            if n<len(_name):                
                _ax.errorbar(x=df['Memo']*screw_pitch/51200.0,
                             y=df[_name[n]+'.mean'],
                             yerr=df[_name[n]+'.std'],
                             fmt='ko',label=_name[n],
                             markersize=2,capsize=3)
                _ax.legend(fontsize=7)
            else:
                break
    plt.show()
    plt.savefig('hoge.png')
    plt.close()

'''
    #plt.savefig('hoge.png')
'''
def init(epicschannel):
    f=open(epicschannel,'r',encoding='UTF-8')
    chname = f.readlines()
    f.close()
    chname = [name[:-1] for name in chname if name[0]!='#'] 
    chname = [ name.split(',') if ',' in name else [name, 999] for name in chname]
    plotnum = [int(i[1]) for i in chname]
    chname = [i[0] for i in chname]
    return plotnum, chname

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description='hoge')
    parser.add_argument('args1')
    parser.add_argument('-m','--memo')
    parser.add_argument('-f','--output',default='result.txt')
    parser.add_argument('-l','--epicschannel')
    parser.add_argument('-s','--screw_pitch',default = 1.0)
    args = parser.parse_args()
    memo = args.memo
    screw_pitch = args.screw_pitch
    print('screw_pitch :',screw_pitch)
    
    if args.args1=='add':
        plotnum, chname = init(args.epicschannel)

        now = datetime.now()
        avg = np.array(avg(1,chname,stddev=True))
        data = [[str(now),memo,*list(map(lambda x:'{0:.3f}'.format(x),avg.flatten()))]]
        #print(data[0])
        txt = ','.join(data[0])+'\n'
        #print(txt)
        
        with open(args.output,'a') as f:
            f.write(txt)
        plot(args.output)

    elif args.args1=='new':
        plotnum, chname = init(args.epicschannel)
        name = np.array([[ch+'.mean',ch+'.std'] for ch in chname]).flatten()
        txt = 'DateTime,Memo,'+','.join(name)+'\n'
        with open(args.output,'w') as f:
            f.write(txt)

        now = datetime.now()
        avg = np.array(avg(1,chname,stddev=True))
        data = [[str(now),memo,*list(map(lambda x:'{0:.3f}'.format(x),avg.flatten()))]]
        #print(data[0])
        txt = ','.join(data[0])+'\n'
        #print(txt)
        with open(args.output,'a') as f:
            f.write(txt)
        #print(len(data))
        plot(args.output)
        
    elif args.args1=='plot':
        plotnum, chname = init(args.epicschannel)
        plot(args.output)


