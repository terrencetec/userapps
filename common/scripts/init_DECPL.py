from ezca import Ezca
import sys

ezca = Ezca()

OPTIC = sys.argv[1]



initMatrix = {'ITMY':{'MN':[[1,0,0,0,0,0],
                            [0,0,0,1,0,0],
                            [0,0,0,0,0,0],
                            [0,1,0,0,0,0],
                            [0,0,0,0,1,0],
                            [0,0,0,0,0,1]],
                      'IM':[[1,0,0,0,0,0],
                            [0,0,0,1,0,0],
                            [0,0,0,0,0,0],
                            [0,1,0,0,0,0],
                            [0,0,0,0,1,0],
                            [0,0,0,0,0,1]],
                      'BF':[[1,0,0,0,0,0],
                            [0,1,0,0,0,0],
                            [0,0,0,0,0,0],
                            [0,0,0,0,0,0],
                            [0,0,0,0,0,0],
                            [0,0,0,0,0,1]],
                      'IP':[[1,0,0,0,0,0],
                            [0,1,0,0,0,0],
                            [0,0,1,0,0,0],
                            [0,0,0,1,0,0],
                            [0,0,0,0,1,0],
                            [0,0,0,0,0,1]],
                      'TM':[[1,0,0,0,0,0],
                            [0,1,0,0,0,0],
                            [0,0,1,0,0,0],
                            [0,0,0,1,0,0],
                            [0,0,0,0,1,0],
                            [0,0,0,0,0,1]]
                      },
              }



for stage in initMatrix[OPTIC].keys():
    for ii in range(6):
        for jj in range(6):
            if not ezca['VIS-%s_MTRX_LOCK'%OPTIC]:
                ezca['VIS-%s_DIAG_DECPL_%s_%d_%d'%(OPTIC,stage,ii+1,jj+1)] = initMatrix[OPTIC][stage][ii][jj]
                ezca['MOD-%s_DIAG_DECPL_%s_%d_%d'%(OPTIC,stage,ii+1,jj+1)] = initMatrix[OPTIC][stage][ii][jj]
