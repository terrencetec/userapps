import sys
from ezca import Ezca

ezca = Ezca()

def CP_MODEPARAMS(OPTIC, copychan):
    copyPrefix = 'VIS-%s_%s_'%(OPTIC,copychan)
    origin_mode = ezca[copyPrefix + 'USER_DESCRIPTION']
    originPrefix = 'VIS-%s_FREE_MODE_LIST_NO%d_'%(OPTIC,int(origin_mode))


    paramlist = ['FREQ','Q_VAL','DECAY_TIME','PRE_FREQ','PRE_Q','DEGEN_MODE','PLL_SENS','DOF']
    paramlist += ['MEAS_DATE_' + a for a in ['YEAR','MON','DAY']]
    paramlist += ['CP_COEF_' + a for a in ['IP','BF','MN','IM','TM']]
    paramlist += ['REL_PHASE_' + a for a in ['IP','BF','MN','IM','TM']]

    paramlist += ['%s_CP_COEF_%s'%(a,b) for a in ['IP','BF','MN','IM','TM'] for b in ['LEN','TRA','VER','ROL','PIT','YAW']]
    paramlist += ['%s_REL_PHASE_%s'%(a,b) for a in ['IP','BF','MN','IM','TM'] for b in ['LEN','TRA','VER','ROL','PIT','YAW']]

    for param in paramlist:
        ezca[copyPrefix + param] = ezca[originPrefix + param]
                  
if __name__ == '__main__':
    CP_MODEPARAMS(sys.argv[1],sys.argv[2])
    
