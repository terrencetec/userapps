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

def grd_mini(x,y,system='ETMX'):
    width = 270
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
    "composite file"="{common}/medm/OVERVIEW/MINI/GRD_MINI.adl;SYSTEM={system}"
    }}
    '''.format(common=common,x=x,y=y,system=system)
    return txt,width,height


def sdf_mini(x,y,fec='123',subsys='ETMXT'):
    width = 260
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

def gds_mini(x,y,fec='123',subsys='ETMXT'):
    width = 150
    height = 15
    subsys = subsys.lower()
    SUBSYS = subsys.upper()    
    txt = '''
    composite {{
    object {{
    x={x}
    y={y}
    width=260
    height=15
    }}
    "composite name"=""
    "composite file"="{common}/medm/OVERVIEW/MINI/GDS_MINI.adl;FEC={fec},SUBSYS={SUBSYS},subsys={subsys}"
    }}
    '''.format(common=common,x=x,y=y,fec=fec,subsys=subsys,SUBSYS=SUBSYS)
    return txt,width,height


def usr_mini(x,y,fec='123',system='ETMX'):
    width = 290
    height = 15
    txt = '''
    composite {{
    object {{
    x={x}
    y={y}
    width=260
    height=15
    }}
    "composite name"=""
    "composite file"="{common}/medm/OVERVIEW/MINI/USER_MINI.adl;FEC={fec},SYSTEM={system}"
    }}
    '''.format(common=common,x=x,y=y,fec=fec,system=system)
    return txt,width,height



if __name__=='__main__':
    systems = ['ETMX','ETMY','ITMX','ITMY','BS','SRM','SR2','SR3','PRM',
               'PR2','PR3','MCI','MCE','MCO','IMMT1','IMMT2','OMMT1','OMMT2',
               'OSTM','TMSX','TMSY']
    models = {'ETMX':[['VISETMXT',68],['VISETMXP',69],['VISETMXMON',79],['MODALETMX',86]],
              'ETMY':[['VISETMYT',65],['VISETMYP',64],['VISETMYMON',80],['MODALETMY',89]],
              'ITMX':[['VISITMXT',66],['VISITMXP',67],['VISITMXMON',77],['MODALITMX',70]],
              'ITMY':[['VISITMYT',62],['VISITMYP',63],['VISITMYMON',78],['MODALITMY',11]],
              'BS':[['VISBST',93],['VISBSP',92]],
              'SRM':[['VISSRMT',58],['VISSRMP',59]],
              'SR2':[['VISSR2T',54],['VISSR2P',55]],
              'SR3':[['VISSR3T',56],['VISSR3P',57]],
              'PRM':[['VISPRM',24]],
              'PR2':[['VISPR2',91]],
              'PR3':[['VISPR3',23]],
              'MCI':[['VISMCI',34]],
              'MCE':[['VISMCE',35]],
              'MCO':[['VISMCO',36]],
              'IMMT1':[['VISIMMT1',81]],
              'IMMT2':[['VISIMMT2',82]],
              'OMMT1':[['VISOMMT1',83]],
              'OMMT2':[['VISOMMT2',84]],
              'OSTM':[['VISOSTM',87]],
              'TMSX':[['VISTMSX',107]],
              'TMSY':[['VISTMSY',114]],              
    }
    
    height = 10
    width = 10
    contents = header    
    with open('./MINI/VIS_MINI.adl','w') as f:
        for system in systems:
            model,fec = models[system][0]
            txt,w1,h1 = usr_mini(x=width,y=height,system=system)
            contents += txt            
            width += w1+2
            txt,w2,h = grd_mini(x=width,y=height,system='VIS_'+system)
            contents += txt
            width += w2+2
            # if system in ['ETMX','ETMY','ITMX','ITMY']:
            #     txt,w3,h = grd_mini(x=width,y=height,system='QUA_'+system)
            #     contents += txt                
            #     txt,w3,h = grd_mini(x=width,y=height+(h+2),system='NEW_'+system)
            #     contents += txt                
            #     width += w3+2
            #     _w = w1+w2+w3+6
            # else:
            #     width += w2+2
            _w = w1+w2+4
            for model in models[system]:
                model,fec = model
                txt,w,h = sdf_mini(x=width,y=height,fec=fec,subsys=model)
                contents += txt
                txt,w,h = gds_mini(x=width+w+2,y=height,fec=fec,subsys=model)
                contents += txt                
                height += h+2
            if len(models[system])==1:
                height += h
            width -= _w
            
        f.write(contents)    
