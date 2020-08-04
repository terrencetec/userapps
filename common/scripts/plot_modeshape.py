# plot sensing vector measured by PreQua
# 2020/08/02 by MN

import numpy as np
import matplotlib.pyplot as plt
from ezca import Ezca
from mpl_toolkits.mplot3d import Axes3D
import sys


def plot_mode(ezca,stage,OPTIC,axis,modelist_str=[],DoFlist=[],fig=plt.figure(),subplotpos=(1,1,1)):

    _modelist = modelist_str.split(',')
    modelist = []
    for strnum in _modelist:
        try:
            modelist.append(int(strnum))
        except:
            pass

    for ii in range(1,25):
        DoF = ezca['VIS-%s_FREE_MODE_LIST_NO%d_DOF'%(OPTIC,ii)]
        if DoF in DoFlist and not DoF == '':
            modelist.append(ii)
                
    if len(modelist) == 0:
        modelist = range(1,25)

                
    if len(axis) == 2:
        ax = fig.add_subplot(*subplotpos)
        for modeindex in modelist:
            amp_x = ezca['VIS-%s_FREE_MODE_LIST_NO%d_%s_CP_COEF_%s'%(OPTIC,modeindex,stage,axis[0])]
            amp_y = ezca['VIS-%s_FREE_MODE_LIST_NO%d_%s_CP_COEF_%s'%(OPTIC,modeindex,stage,axis[1])]
            theta_x = ezca['VIS-%s_FREE_MODE_LIST_NO%d_%s_REL_PHASE_%s'%(OPTIC,modeindex,stage,axis[0])]
            theta_y = ezca['VIS-%s_FREE_MODE_LIST_NO%d_%s_REL_PHASE_%s'%(OPTIC,modeindex,stage,axis[1])]

            freq = ezca['VIS-%s_FREE_MODE_LIST_NO%d_FREQ'%(OPTIC,modeindex)]
            DoF = ezca['VIS-%s_FREE_MODE_LIST_NO%d_DOF'%(OPTIC,modeindex)]
            
            theta = np.arange(0,2*np.pi,2*np.pi/100.)
            
            x = amp_x*np.cos(theta+np.deg2rad(theta_x))
            y = amp_y*np.cos(theta+np.deg2rad(theta_y))
            ax.plot(x,y,label='%s %.2f Hz'%(DoF,freq))
            
        ax.set_xlim(-1,1)
        ax.set_ylim(-1,1)
        ax.set_aspect('equal')
        ax.set_xlabel(axis[0])
        ax.set_ylabel(axis[1])



    elif len(axis)>2:
        ax = fig.add_subplot(*subplotpos,projection='3d')
        
        for modeindex in modelist:
            amp_x = ezca['VIS-%s_FREE_MODE_LIST_NO%d_%s_CP_COEF_%s'%(OPTIC,modeindex,stage,axis[0])]
            amp_y = ezca['VIS-%s_FREE_MODE_LIST_NO%d_%s_CP_COEF_%s'%(OPTIC,modeindex,stage,axis[1])]
            amp_z = ezca['VIS-%s_FREE_MODE_LIST_NO%d_%s_CP_COEF_%s'%(OPTIC,modeindex,stage,axis[2])]
            theta_x = ezca['VIS-%s_FREE_MODE_LIST_NO%d_%s_REL_PHASE_%s'%(OPTIC,modeindex,stage,axis[0])]
            theta_y = ezca['VIS-%s_FREE_MODE_LIST_NO%d_%s_REL_PHASE_%s'%(OPTIC,modeindex,stage,axis[1])]
            theta_z = ezca['VIS-%s_FREE_MODE_LIST_NO%d_%s_REL_PHASE_%s'%(OPTIC,modeindex,stage,axis[2])]

            theta = np.arange(0,2*np.pi,2*np.pi/100.)
        
            x = amp_x*np.cos(theta+np.deg2rad(theta_x))
            y = amp_y*np.cos(theta+np.deg2rad(theta_y))
            z = amp_z*np.cos(theta+np.deg2rad(theta_z))

            ax.plot(x,y,z)
            
        ax.set_xlim(-1,1)
        ax.set_ylim(-1,1)
        ax.set_zlim(-1,1)
        ax.set_aspect('equal')
        ax.set_xlabel(axis[0])
        ax.set_ylabel(axis[1])
        ax.set_zlabel(axis[2])


    return fig, ax


        
                          
if __name__ == '__main__':
    ezca = Ezca()
    
    modelist = ezca['PLA-SCRIPT_ARG1']
    DoFlist = ezca['PLA-SCRIPT_ARG2']
    OPTIC = sys.argv[1]
    stage = sys.argv[2]
    filename = sys.argv[3]

    fig = plt.figure(tight_layout=True,)
    if stage == 'TM':
        fig,ax1 = plot_mode(ezca,stage,OPTIC,['YAW','PIT'],modelist_str=modelist,DoFlist=DoFlist,fig=fig,subplotpos=(1,3,1))
        fig,ax2 = plot_mode(ezca,stage,OPTIC,['PIT','LEN'],modelist_str=modelist,DoFlist=DoFlist,fig=fig,subplotpos=(1,3,2))
        fig,ax3 = plot_mode(ezca,stage,OPTIC,['YAW','LEN'],modelist_str=modelist,DoFlist=DoFlist,fig=fig,subplotpos=(1,3,3))
        ax3.legend(fontsize=10,bbox_to_anchor=(2,1))
        #fig,ax4 = plot_mode(ezca,stage,OPTIC,['YAW','LEN','PIT'],modelist_str=modelist,DoFlist=DoFlist,fig=fig,subplotpos=(1,4,4))

    elif stage == 'IP':
        fig,ax1 = plot_mode(ezca,stage,OPTIC,['TRA','LEN'],modelist_str=modelist,DoFlist=DoFlist,fig=fig,subplotpos=(1,3,1))
        fig,ax2 = plot_mode(ezca,stage,OPTIC,['LEN','YAW'],modelist_str=modelist,DoFlist=DoFlist,fig=fig,subplotpos=(1,3,2))
        fig,ax3 = plot_mode(ezca,stage,OPTIC,['TRA','YAW'],modelist_str=modelist,DoFlist=DoFlist,fig=fig,subplotpos=(1,3,3))
        ax3.legend(fontsize=10,bbox_to_anchor=(2,1))
        #fig,ax4 = plot_mode(ezca,stage,OPTIC,['YAW','LEN','PIT'],modelist_str=modelist,DoFlist=DoFlist,fig=fig,subplotpos=(1,4,4))

    else:
        fig,ax1 = plot_mode(ezca,stage,OPTIC,['TRA','LEN'],modelist_str=modelist,DoFlist=DoFlist,fig=fig,subplotpos=(2,3,1))
        fig,ax2 = plot_mode(ezca,stage,OPTIC,['LEN','VER'],modelist_str=modelist,DoFlist=DoFlist,fig=fig,subplotpos=(2,3,2))
        fig,ax3 = plot_mode(ezca,stage,OPTIC,['TRA','VER'],modelist_str=modelist,DoFlist=DoFlist,fig=fig,subplotpos=(2,3,3))
        fig,ax4 = plot_mode(ezca,stage,OPTIC,['YAW','PIT'],modelist_str=modelist,DoFlist=DoFlist,fig=fig,subplotpos=(2,3,4))
        fig,ax5 = plot_mode(ezca,stage,OPTIC,['YAW','ROL'],modelist_str=modelist,DoFlist=DoFlist,fig=fig,subplotpos=(2,3,5))
        fig,ax6 = plot_mode(ezca,stage,OPTIC,['ROL','PIT'],modelist_str=modelist,DoFlist=DoFlist,fig=fig,subplotpos=(2,3,6))
        ax3.legend(fontsize=10,bbox_to_anchor=(2,1))
    plt.savefig(filename,bbox_inches="tight")
