import numpy as np
from ezca import Ezca
import sys
ezca = Ezca()
OPTIC = sys.argv[1]
stage = sys.argv[2]

if stage == 'GAS':
    for jj in range(1,6):
        modeindex = int(ezca['PRE-%s_SENSDIAG_GAS_MODEINDEX_M%d'%(OPTIC,jj)])
        for ii in range(1,6):
            ezca['PRE-%s_SENSDIAG_GAS_RATIO_%d_%d'%(OPTIC,ii,jj)] = ezca['PRE-%s_MODE_GAS_NO%d_STAGE_MOTION_RATIO_%d_1'%(OPTIC,modeindex,ii)]
            ezca['PRE-%s_SENSDIAG_GAS_PHASE_%d_%d'%(OPTIC,ii,jj)] = ezca['PRE-%s_MODE_GAS_NO%d_STAGE_MOTION_PHASE_%d_1'%(OPTIC,modeindex,ii)]
            
            
    
