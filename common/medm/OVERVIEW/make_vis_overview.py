header = '''
file {
	name="/opt/rtcds/userapps/release/vis/common/medm/OVERVIEW/VIS_MINI.adl"
	version=030107
}
display {
	object {
		x=1996
		y=56
		width=1360
		height=958
	}
	clr=14
	bclr=13
	cmap=""
	gridSpacing=5
	gridOn=0
	snapToGrid=0
}
"color map" {
	ncolors=65
	colors {
		ffffff,
		ececec,
		dadada,
		c8c8c8,
		bbbbbb,
		aeaeae,
		9e9e9e,
		919191,
		858585,
		787878,
		696969,
		5a5a5a,
		464646,
		2d2d2d,
		000000,
		00d800,
		1ebb00,
		339900,
		2d7f00,
		216c00,
		fd0000,
		de1309,
		be190b,
		a01207,
		820400,
		5893ff,
		597ee1,
		4b6ec7,
		3a5eab,
		27548d,
		fbf34a,
		f9da3c,
		eeb62b,
		e19015,
		cd6100,
		ffb0ff,
		d67fe2,
		ae4ebc,
		8b1a96,
		610a75,
		a4aaff,
		8793e2,
		6a73c1,
		4d52a4,
		343386,
		c7bb6d,
		b79d5c,
		a47e3c,
		7d5627,
		58340f,
		99ffff,
		73dfff,
		4ea5f9,
		2a63e4,
		0a00b8,
		ebf1b5,
		d4db9d,
		bbc187,
		a6a462,
		8b8239,
		73ff6b,
		52da3b,
		3cb420,
		289315,
		1a7309,
	}
}
'''

common = '/opt/rtcds/userapps/release/vis/common'

def grd_mini(x,y,SYSTEM='VIS_ETMX',OPTIC='ETMX'):
    width = 150
    height = 25
    txt = '''
    composite {{
    object {{
    x={x}
    y={y}
    width=300
    height=15
    }}
    "composite name"=""
    "composite file"="{common}/medm/OVERVIEW/MINI/GRD_MINI.adl;SYSTEM={SYSTEM},OPTIC={OPTIC}"
    }}
    '''.format(common=common,x=x,y=y,SYSTEM=SYSTEM,OPTIC=OPTIC)
    return txt,width,height

def optic_mini(x,y,SYSTEM='VIS_ETMX',OPTIC='ETMX'):
    '''
    '''
    width = 65
    height = 25
    txt = '''
    composite {{
    object {{
    x={x}
    y={y}
    width=300
    height=15
    }}
    "composite name"=""
    "composite file"="{common}/medm/OVERVIEW/MINI/OPTIC_MINI.adl;SYSTEM={SYSTEM},OPTIC={OPTIC}"
    }}
    '''.format(common=common,x=x,y=y,SYSTEM=SYSTEM,OPTIC=OPTIC)
    return txt,width,height


def sdf_mini(x,y,fec='123',subsys='ETMXT'):
    width = 250
    height = 15
    subsys = subsys.lower()
    SUBSYS = subsys.upper()
    txt = '''
    composite {{
    object {{
    x={x}
    y={y}
    width=200
    height=15
    }}
    "composite name"=""
    "composite file"="{common}/medm/OVERVIEW/MINI/SDF_MINI.adl;FEC={fec},SUBSYS={SUBSYS},subsys={subsys}"
    }}
    '''.format(common=common,x=x,y=y,fec=fec,subsys=subsys,SUBSYS=SUBSYS)
    return txt,width,height

def ctrl_mini(x,y,fec='123',ifo='K1',optic='ETMX',subsys='ETMXT'):
    '''
    '''
    width = 250
    height = 15
    if subsys[-1]=='T':
        adl = 'CTRL_TWR_MINI.adl'
    else:
        if OPTIC in ['ETMX','ETMY','ITMX','ITMY']:
            adl = 'CTRL_CRYOPAY_MINI.adl'
        elif OPTIC in ['BS','SRM','SR2','SR3','PR2','PR3','PRM']:            
            adl = 'CTRL_ROOMPAY_MINI.adl'
        else:
            adl = 'CTRL_TAMAPAY_MINI.adl'    
    txt = '''
    composite {{
    object {{
    x={x}
    y={y}
    width=200
    height=15
    }}
    "composite name"=""
    "composite file"="{common}/medm/OVERVIEW/MINI/{adl};FEC={fec},IFO={ifo},OPTIC={optic},subsys={subsys}"
    }}
    '''.format(adl=adl,common=common,x=x,y=y,fec=fec,ifo=ifo,optic=optic,subsys=subsys)
    return txt,width,height


def gds_mini(x,y,fec='123',optic='ETMX',subsys='ETMXT',part='TWR'):
    width = 150
    height = 15
    subsys = subsys.lower()
    SUBSYS = subsys.upper()
    system = subsys
    optic = optic.lower()
    OPTIC = optic.upper()
    txt = '''
    composite {{
    object {{
    x={x}
    y={y}
    width=260
    height=15
    }}
    "composite name"=""
    "composite file"="{common}/medm/OVERVIEW/MINI/GDS_MINI.adl;FEC={fec},SUBSYS={SUBSYS},subsys={subsys},PART={part},K1SUBSYS={K1SUBSYS},system={subsys}"
    }}
    '''.format(common=common,x=x,y=y,fec=fec,subsys=subsys,SUBSYS=SUBSYS,part=part,K1SUBSYS='K1'+SUBSYS)
    return txt,width,height

def wd_mini(x,y,fec='123',optic='ETMX',subsys='ETMXT',part='TWR'):
    width = 320
    height = 15
    subsys = subsys.lower()
    SUBSYS = subsys.upper()
    system = subsys
    optic = optic.lower()
    OPTIC = optic.upper()
    if SUBSYS[-1]=='T':
        adl = 'WD_TWR_MINI.adl'
    else:
        if OPTIC in ['ETMX','ETMY','ITMX','ITMY']:
            adl = 'WD_CRYOPAY_MINI.adl'
        elif OPTIC in ['BS','SRM','SR2','SR3','PR2','PR3','PRM']:            
            adl = 'WD_ROOMPAY_MINI.adl'
        else:
            adl = 'WD_TAMAPAY_MINI.adl'
    txt = '''
    composite {{
    object {{
    x={x}
    y={y}
    width=260
    height=15
    }}
    "composite name"=""
    "composite file"="{common}/medm/OVERVIEW/MINI/{adl};OPTIC={OPTIC}"
    }}
    '''.format(adl=adl,common=common,x=x,y=y,OPTIC=OPTIC)        
    return txt,width,height


def user_mini(x,y,fec='123',OPTIC='ETMX',suffix='TOWER_OVERVIEW'):
    width = 350
    height = 25
    sustype = sus_type_is(OPTIC).lower()
    SUSTYPE = sustype.upper()
    optic = OPTIC.lower()
    OPTIC = OPTIC.upper()
    adltype='USER_MINI.adl'
    txt = '''
    composite {{
    object {{
    x={x}
    y={y}
    width=260
    height=15
    }}
    "composite name"=""
    "composite file"="{common}/medm/OVERVIEW/MINI/{adltype};FEC={fec},OPTIC={OPTIC}"
    }}
    '''.format(common=common,x=x,y=y,adltype=adltype,fec=fec,OPTIC=OPTIC,sustype=sustype,suffix=suffix,SUSTYPE=SUSTYPE)
    return txt,width,height

def trip_mini(x,y,optic='ETMX'):
    width = 150
    height = 25
    sus_type = sus_type_is(optic)
    txt = '''
    composite {{
    object {{
    x={x}
    y={y}
    width=148
    height=30
    }}
    "composite name"=""
    "composite file"="{mini_name};OPTIC={optic}"
    }}
    '''.format(common=common,x=x,y=y,mini_name=trip_mini_name_is(optic),optic=optic)
    return txt,width,height


if __name__=='__main__':
    no_installed_date_model = ['VISETMXMON','VISETMYMON','VISITMXMON','VISITMYMON',
                               'MODALETMX','MODALETMY','MODALITMX','MODALITMY']
    optics = ['ETMX','ETMY','ITMX','ITMY','BS','SRM','SR2','SR3','PRM',
               'PR2','PR3','MCI','MCE','MCO','IMMT1','IMMT2','OMMT1','OMMT2',
               'OSTM','TMSX','TMSY']
    
    models = {'ETMX':[['VISETMXT',102],['VISETMXP',103]],
              'ETMY':[['VISETMYT',107],['VISETMYP',108]],
              'ITMX':[['VISITMXT',92],['VISITMXP',93]],
              'ITMY':[['VISITMYT',97],['VISITMYP',98]],
              'BS':[['VISBST',60],['VISBSP',61]],
              'SRM':[['VISSRMT',75],['VISSRMP',76]],
              'SR2':[['VISSR2T',65],['VISSR2P',66]],
              'SR3':[['VISSR3T',70],['VISSR3P',71]],
              'PRM':[['VISPRMT',55],['VISPRMP',56]],
              'PR2':[['VISPR2T',45],['VISPR2P',46]],
              'PR3':[['VISPR3T',50],['VISPR3P',51]],
              'MCI':[['VISMCI',38]],
              'MCE':[['VISMCE',39]],
              'MCO':[['VISMCO',40]],
              'IMMT1':[['VISIMMT1',42]],
              'IMMT2':[['VISIMMT2',43]],
              'OMMT1':[['VISOMMT1',80]],
              'OMMT2':[['VISOMMT2',81]],
              'OSTM':[['VISOSTM',82]],
              'TMSX':[['VISTMSX',113]],
              'TMSY':[['VISTMSY',122]],              
    }
    sus_types = {'TypeA':['ETMX','ETMY','ITMX','ITMY'],
                'TypeB':['BS','SR2','SR3','SRM'],
                'TypeBp':['PR2','PR3','PRM'],
                'TypeC-IMC':['MCI','MCO','MCE','IMMT1','IMMT2'],
                'TypeC-OMC':['OSTM','OMMT1','OMMT2'],                 
                'TypeTMS':['TMSX','TMSY']}
    
    def sus_type_is(optic):
        for sus_type in ['TypeA','TypeB','TypeBp','TypeC-IMC','TypeC-OMC','TypeTMS']:
            if optic in sus_types[sus_type]:
                return sus_type
            else:
                pass
        return None
    
    def trip_mini_name_is(optic):
        sus_type = sus_type_is(optic)
        if sus_type == 'TypeA':
            adl = './MINI/tripped_microA.adl'
        elif sus_type == 'TypeB':
            adl = './MINI/tripped_microB.adl'
        elif sus_type == 'TypeBp':
            adl = './MINI/tripped_microBp.adl'            
        elif sus_type == 'TypeC-IMC':
            adl = './MINI/tripped_microC.adl'
        elif sus_type == 'TypeC-OMC':
            adl = './MINI/tripped_microC.adl'                        
        elif sus_type == 'TypeTMS':
            adl = './MINI/tripped_microT.adl'            
        else:
            raise ValueError('!')        
        return adl
    
        
    height = 10
    width = 2
    contents = header    
    with open('./MINI/VIS_MINI.adl','w') as f:
        for optic in optics:
            OPTIC = optic.upper()
            model,fec = models[optic][0]
            txt,w0,h0 = optic_mini(x=width,y=height,SYSTEM='VIS_'+OPTIC,OPTIC=OPTIC)
            contents += txt
            width += w0+5            
            txt,w1,h1 = grd_mini(x=width,y=height,SYSTEM='VIS_'+OPTIC,OPTIC=OPTIC)
            contents += txt            
            width += w1+5
            txt,w2,h = user_mini(x=width,y=height,OPTIC=OPTIC)
            contents += txt
            width += w2+5
            _w = w0+w1+w2+4
            #txt,w3,h = trip_mini(x=width,y=height,optic=optic)
            #contents += txt
            #width += w3+5
            _w = w0+w1+w2+15
            for model in models[optic]:
                model,fec = model
                txt,w,h = ctrl_mini(x=width,y=height,fec=fec,optic=optic,subsys=model)
                contents += txt                
                txt,w,h = sdf_mini(x=width,y=height,fec=fec,subsys=model)
                contents += txt
                txt,w,h = wd_mini(x=width+w+5,y=height,fec=fec,subsys=model,
                                   optic=optic)
                contents += txt                
                txt,w,h = gds_mini(x=width+w+5,y=height,fec=fec,subsys=model,
                                   optic=optic)
                contents += txt                
                height += h+2
            try:
                if len(models[optic])==1:
                    height += h
            except:
                pass
            
            width -= _w
            
        f.write(contents)    
