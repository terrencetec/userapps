import numpy as np
from ezca import Ezca
import sys
ezca = Ezca()
OPTIC = sys.argv[1]
stage = sys.argv[2]

DoFs = ['LEN','TRA','VER','ROL','PIT','YAW']
Stages = {'IP':1,'BF':2,'MN':3,'IM':4,'TM':5}

if stage == 'GAS':
    for jj in range(1,6):
        try:
            modeindex = int(ezca['PRE-%s_SENSDIAG_GAS_MODEINDEX_M%d'%(OPTIC,jj)])
            for ii in range(1,6):
                ezca['PRE-%s_SENSDIAG_GAS_RATIO_%d_%d'%(OPTIC,ii,jj)] = ezca['PRE-%s_MODE_GAS_NO%d_STAGE_MOTION_RATIO_%d_1'%(OPTIC,modeindex,ii)]
                ezca['PRE-%s_SENSDIAG_GAS_PHASE_%d_%d'%(OPTIC,ii,jj)] = ezca['PRE-%s_MODE_GAS_NO%d_STAGE_MOTION_PHASE_%d_1'%(OPTIC,modeindex,ii)]
        except:
            for ii in range(1,6):
                ezca['PRE-%s_SENSDIAG_GAS_RATIO_%d_%d'%(OPTIC,ii,jj)] = 0
                ezca['PRE-%s_SENSDIAG_GAS_PHASE_%d_%d'%(OPTIC,ii,jj)] = 0

            
else:
    for jj in range(1,7):
        try:
            modeindex = int(ezca['PRE-%s_SENSDIAG_%s_MODEINDEX_%s'%(OPTIC,stage,DoFs[jj-1])])
            for ii in range(1,7):
                ezca['PRE-%s_SENSDIAG_%s_AMP_%d_%d'%(OPTIC,stage,ii,jj)] = ezca['PRE-%s_MODE_NO%d_SENSMAT_RATIO_%d_%d'%(OPTIC,modeindex,ii,Stages[stage])]
                ezca['PRE-%s_SENSDIAG_%s_PHASE_%d_%d'%(OPTIC,stage,ii,jj)] = ezca['PRE-%s_MODE_NO%d_SENSMAT_PHASE_%d_%d'%(OPTIC,modeindex,ii,Stages[stage])]
                
        except:
            for ii in range(1,7):
                ezca['PRE-%s_SENSDIAG_%s_AMP_%d_%d'%(OPTIC,stage,ii,jj)] = 0
                ezca['PRE-%s_SENSDIAG_%s_PHASE_%d_%d'%(OPTIC,stage,ii,jj)] = 0
            
    
