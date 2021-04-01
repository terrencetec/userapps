import ezca
ezca = ezca.Ezca(timeout=2)

from utils import partname_is
from utils import Ezff, copy_FMs
from utils import switch_on
chans = '/opt/rtcds/kamioka/k1/chans/'
# ------------------------------------------------------------------------------

def init_wd(optics,stage='BF',func='WD_AC_BANDLIM_LVDT',mask=None):
    '''
    '''
    #init_wd(optics,'TM','WD_OPLEVAC_BANDLIM_TILT',mask_wd_ac)

    if 'OPLEV' in func:
        _,_type = func.split('_')
        func1 = 'WD_OPLEVAC_RMS_MAX'
        func2 = 'WD_OPLEVAC_BANDLIM_{0}'.format(_type)
    elif 'OSEM' in func:
        func1 = 'WD_OSEMAC_RMS_MAX'
        func2 = 'WD_OSEMAC_BANDLIM'
    elif 'LVDT' in func:
        if stage in ['F0','F1','F2','F3','SF']:
            func1 = 'WD_AC_RMS_MAX'
            func2 = 'WD_AC_BANDLIM'
        if stage in ['BF']:
            func1 = 'WD_AC_RMS_MAX'
            func2 = 'WD_AC_BANDLIM_LVDT'
        elif stage=='IP':
            func1 = 'WD_AC_RMS_MAX_LVDT'
            func2 = 'WD_AC_BANDLIM_LVDT'            
    elif 'ACC' in func:
        func1 = 'WD_AC_RMS_MAX_{0}'.format(func)
        func2 = 'WD_AC_BANDLIM_{0}'.format(func)
    else:
        raise ValueError('!')

    # Set threshold
    for optic in optics:
        chname = 'VIS-{0}_{1}_{2}'.format(optic,stage,func1)
        if stage=='IP':
            ezca[chname] = 2000
        else:
            ezca[chname] = 100

    # original
    part = partname_is('ETMX',stage)
    ffname = chans + 'K1VISETMX{1}.txt'.format(optic,part)
    ff = Ezff(ffname)
    if stage in ['F0','F1','F2','F3','SF']:
        fmname = 'ETMX_F0_WD_AC_BANDLIM_GAS'
    elif stage in ['MN','IM']:
        fmname = 'ETMX_MN_WD_OSEMAC_BANDLIM_H1'
    elif stage in ['IP','BF']:
        fmname = 'ETMX_IP_WD_AC_BANDLIM_LVDT_H1'
    elif stage in ['TM']:
        fmname = 'ETMX_TM_WD_OPLEVAC_BANDLIM_LEN_SEG1'
    else:
        raise ValueError('!')
    fm_v1 = ff[fmname]
    
    # copy
    _dofdict = {'BF':['H1','H2','H3','V1','V2','V3','GAS'],
                'TM':['SEG1','SEG2','SEG3','SEG4'],
                'IM':['H1','H2','H3','V1','V2','V3'],
                'MN':['H1','H2','H3','V1','V2','V3'],
                'IP':['H1','H2','H3'],
                'F0':['GAS'],
                'F1':['GAS'],
                'F2':['GAS'],
                'F3':['GAS'],
                'SF':['GAS']}    
    for optic in optics:
        part = partname_is(optic,stage)
        ffname = chans + 'K1VIS{0}{1}.txt'.format(optic,part)
        ff = Ezff(ffname)
        # copy to other FMs
        fms = []
        for dof in _dofdict[stage]:
            switch_on('VIS-{0}_{1}_{2}_{3}'.format(optic,stage,func2,dof),mask=mask)
            fmname = '{0}_{1}_{2}_{3}'.format(optic,stage,func2,dof)
            fms += [ff[fmname]]
        copy_FMs(fm_v1,fms)     
        ff.save()


def _oplevmat(optic,stage,func):
    ''' Return the oplev matrices. 

    Parameters
    ----------
    stage: `str`
        stage name.
    func: `str`
        function name of the OpLev. e.g. OPLEV_TILT

    Returns
    -------
    _seg2oplev: `array`
        4x4 matrix to convert basis from the four segments basis to the OpLev
        dofs: PIT, YAW, SUM, CRS. Value of the matrix depends on the OpLev 
        funcion. Please refer the document.
    _oplev2eul: `array`
        3x4 matrix which is commonly used to combine OPLEV_TILT and OPLEV_LEN 
        OpLevs to convert the OpLev dofs to Euler basis.
    _sensalign: `array`
        This matrix is used to decouple the sensing coupling. Shape of this
        matrix depends on the stage. If the OpLev of TM and PF stage, shape is
        3x3 for 3 dofs: L,P and Y. If MN stage, shape is 6x6 for 6 dofs L, T, V,
        R, P, Y.
    _qpd2eul: `array`
        This matrix is kind of the _oplev2eul matrix but is used only in MN 
        stage for the OPLEV_ROL, OPLEV_TRA, OPLEV_VER OpLevs. If other stages 
        are given, it returns None.
    
    Reference
    ---------
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

def _osemmat(optic,stage='IM'):
    '''
    '''
    _osem2eul = [[ 0.000, 0.000, 0.000,-1.000, 0.000, 0.000],
                 [ 0.000, 0.000, 0.000, 0.000,-0.500,+0.500],
                 [+0.333,+0.333,+0.333, 0.000, 0.000, 0.000],
                 [ 0.000,-6.014,+6.014, 0.000, 0.000, 0.000],
                 [ 0.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                 [ 0.000, 0.000, 0.000, 0.000, 0.000, 0.000]]
    _sensalign = [[+1.000, 0.000, 0.000, 0.000, 0.000, 0.000],
                  [ 0.000,+1.000, 0.000, 0.000, 0.000, 0.000],
                  [ 0.000, 0.000,+1.000, 0.000, 0.000, 0.000],
                  [ 0.000, 0.000, 0.000,+1.000, 0.000, 0.000],
                  [ 0.000, 0.000, 0.000, 0.000,+1.000, 0.000],
                  [ 0.000, 0.000, 0.000, 0.000, 0.000,+1.000]]
    return _osem2eul,_sensalign


def _copy(fm_v1,optic,stage,func,dofs):
    '''
    '''
    part = partname_is(optic,stage)
    ffname = chans + 'K1VIS{0}{1}.txt'.format(optic,part)
    ff = Ezff(ffname)
    # copy to other FMs
    fms = []
    for dof in dofs:
        fmname = '{0}_{1}_{2}_{3}'.format(optic,stage,func,dof)
        fms += [ff[fmname]]
    copy_FMs(fm_v1,fms)        
    ff.save()    
        
def _osemfilts():
    '''
    '''
    optic = 'PR3'
    stage = 'IM'
    func = 'OSEMINF'
    part = partname_is(optic,stage)
    ffname = chans + 'K1VIS{0}{1}.txt'.format(optic,part)
    ff = Ezff(ffname)
    fmname = '{0}_{1}_{2}_{3}'.format(optic,stage,func,'V1')
    fm_v1 = ff[fmname]
    return fm_v1
    
def init_osem(optics,stage='IM'):
    ''' Initialize parameters of OSEMs.     

    Parameters
    ----------
    optics: list of `str`
        List of the optic name
    stage: `str`
        Stage name. default is 'IM'
    funcs: list of `str`
        list of the function name.
    '''  

    # Original Filter Module is given by PRM_IM
    fm_v1 = _osemfilts()
    dofs = ['V1','V2','V3','H1','H2','H3']
    for optic in optics:
        _copy(fm_v1,optic,stage,'OSEMINF',dofs)
    
    for optic in optics:
        for row in range(6):
            for col in range(6):
                chname = 'VIS-{0}_{1}_OSEM2EUL_{2}_{3}'.format(optic,stage,row+1,col+1)
                ezca[chname] = _osemmat(optic,stage)[0][row][col] # 0 is for osem2eul

    for optic in optics:
        for row in range(6):
            for col in range(6):
                chname = 'VIS-{0}_{1}_SENSALIGN_{2}_{3}'.format(optic,stage,row+1,col+1)
                ezca[chname] = _osemmat(optic,stage)[1][row][col] # 1 is for sensalign
                

def init_oplev(optics,stage='TM',funcs=['OPLEV_TILT']):
    ''' Initialize parameters of OpLevs

    Parameters
    ----------
    optics: list of `str`
        List of the optic name
    stage: `str`
        Stage name
    funcs: list of `str`
        list of the function name.
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
                    ezca[chname] = _oplevmat(optic,stage,func)[0][row][col] # 0 is for seg2oplev matrix
                
    # Euler matrix 
    for optic in optics:
        for row in range(3):
            for col in range(4):
                chname = "VIS-{0}_{1}_{2}_{3}_{4}".format(optic,stage,'OPLEV2EUL',row+1,col+1)
                ezca[chname] = _oplevmat(optic,stage,func)[1][row][col] # 1 is for oplev2eul matrix
                
    # Sensalign matrix
    if stage=='MN':
        for optic in optics:        
            for row in range(6):
                for col in range(6):                
                    chname = "VIS-{0}_{1}_{2}_{3}_{4}".format(optic,stage,'OLSENSALIGN',row+1,col+1)
                    ezca[chname] = _oplevmat(optic,stage,func)[2][row][col] # 2 is for sensalign matrix
        for optic in optics:                    
            for row in range(3):
                for col in range(6):                
                    chname = "VIS-{0}_{1}_{2}_{3}_{4}".format(optic,stage,'QPD2EUL',row+1,col+1)
                    ezca[chname] = _oplevmat(optic,stage,func)[3][row][col] # 3 is for qpd2eul
    else:
        for optic in optics:        
            for row in range(3):
                for col in range(3):                
                    chname = "VIS-{0}_{1}_{2}_{3}_{4}".format(optic,stage,'SENSALIGN',row+1,col+1)
                    ezca[chname] = _oplevmat(optic,stage,func)[2][row][col] # 2 is for sensalign matrix

                    
                    
