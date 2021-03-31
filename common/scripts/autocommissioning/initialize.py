import ezca
ezca = ezca.Ezca(timeout=2)


def _oplevmat(stage,func):
    '''

    Reference:
     [1] JGW-G2112738-v1, Oplev matrices, Ushiba,    
    '''
    # Matrix for the segment to oplev
    if func in ['OPLEV_TILT']:
        _seg2oplev = [[-1,-1,+1,+1], # [1]
                      [+1,-1,-1,+1],
                      [+1,+1,+1,+1],
                      [+1,-1,+1,-1]]
    elif func in ['OPLEV_LEN']:
        _seg2oplev = [[+1,+1,-1,-1], # [1]
                      [-1,+1,+1,-1],
                      [+1,+1,+1,+1],
                      [+1,-1,+1,-1]]        
    elif func in ['OPLEV_ROL','OPLEV_TRA']:
        _seg2oplev = [[+1,+1,-1,-1], # [1]
                      [+1,-1,-1,+1],
                      [+1,+1,+1,+1],
                      [+1,-1,+1,-1]]
    elif func in ['OPLEV_VER']:
        _seg2oplev = [[-1,-1,+1,+1], # [1]
                      [+1,-1,-1,+1],
                      [+1,+1,+1,+1],
                      [+1,-1,+1,-1]]        
    else:
        raise ValueError('Invalid oplev stage or function: {0} {1}'.format(stage,func))

    # Euler matrix after the seg2oplev
    # oplev2eul is common
    _oplev2eul = [[0,0,0,1],
                  [1,0,0,0],
                  [0,1,0,0]]
    
    # qpd2eul and olsensalign are for only MN OpLev
    if stage=='MN':
        _sensalign = [[1,0,0,0,0,0],
                      [0,1,0,0,0,0],
                      [0,0,1,0,0,0],
                      [0,0,0,1,0,0],
                      [0,0,0,0,1,0],
                      [0,0,0,0,0,1]]
        _qpd2eul = [[0,0,0,1,0,0], # Is it OK?
                    [0,1,0,0,0,0],
                    [0,0,1,0,0,0]] 
    else:
        _sensalign = [[1,0,0],
                      [0,1,0],
                      [0,0,1]]
        _qpd2eul = None
                
    return _seg2oplev,_oplev2eul,_sensalign,_qpd2eul
    

def init_oplev(optics,stage='TM',funcs=['OPLEV_TILT']):
    '''
    '''        
    # Filter bank of SEGs.
    for optic in optics:
        for func in funcs:
            # Set -1 for gain value of QPD
            for segnum in range(4):
                chname = 'VIS-{0}_{1}_{2}_SEG{3}_GAIN'.format(optic,stage,func,segnum+1)
                ezca[chname] = -1
            # Set the de-gain filter?            
            pass # Fix me
        
    # Oplev Matrix
    for optic in optics:
        for func in funcs:        
            for row in range(4):
                for col in range(4):
                    chname = 'VIS-{0}_{1}_{2}_MTRX_{3}_{4}'.format(optic,stage,func,row+1,col+1)
                    ezca[chname] = _oplevmat(stage,func)[0][row][col] # 0 is for seg2oplev matrix
                
    # Euler matrix 
    for optic in optics:
        for row in range(3):
            for col in range(4):
                chname = "VIS-{0}_{1}_{2}_{3}_{4}".format(optic,stage,'OPLEV2EUL',row+1,col+1)
                ezca[chname] = _oplevmat(stage,func)[1][row][col] # 1 is for oplev2eul matrix
                
    # Sensalign matrix
    if stage=='MN':
        #
        for optic in optics:        
            for row in range(6):
                for col in range(6):                
                    chname = "VIS-{0}_{1}_{2}_{3}_{4}".format(optic,stage,'OLSENSALIGN',row+1,col+1)
                    ezca[chname] = _oplevmat(stage,func)[2][row][col] # 2 is for sensalign matrix
        for optic in optics:                    
            for row in range(3):
                for col in range(6):                
                    chname = "VIS-{0}_{1}_{2}_{3}_{4}".format(optic,stage,'QPD2EUL',row+1,col+1)
                    ezca[chname] = _oplevmat(stage,func)[3][row][col] # 3 is for qpd2eul
    else:
        for optic in optics:        
            for row in range(3):
                for col in range(3):                
                    chname = "VIS-{0}_{1}_{2}_{3}_{4}".format(optic,stage,'SENSALIGN',row+1,col+1)
                    ezca[chname] = _oplevmat(stage,func)[2][row][col] # 2 is for sensalign matrix
