

header = '''

file {
	name="/opt/rtcds/userapps/release/vis/common/medm/VIS_OVERVIEW.adl"
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
rectangle {
	object {
		x=315
		y=22
		width=300
		height=70
	}
	"basic attribute" {
		clr=5
	}
}
rectangle {
	object {
		x=320
		y=27
		width=290
		height=60
	}
	"basic attribute" {
		clr=14
	}
}
composite {
	object {
		x=335
		y=56
		width=260
		height=25
	}
	"composite name"=""
	"composite file"="/opt/rtcds/userapps/release/vis/common/scripts/medm/overview/GRD_MINI.adl;SYSTEM=VIS_MANAGER"
}
text {
	object {
		x=428
		y=35
		width=74
		height=16
	}
	"basic attribute" {
		clr=57
	}
	textix="AMATERASU"
	align="horiz. centered"
}
'''

composit = '''
		composite {
			object {
				x=18
				y=116
				width=910
				height=30
			}
			"composite name"=""
			"composite file"="/opt/rtcds/userapps/release/vis/common/scripts/medm/overview/VIS_OVERVIEW_MINI.adl;IFO=K1,ifo=$(ifo),site=$(site), OPTIC=ETMX,subsys=etmxt,SUBSYS=ETMXT, optic=etmxt,FEC=68,SYSTEM=VIS_ETMX"
		}
'''

def grd_mini(x,y,system='ETMX'):
    width = 260
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
    "composite file"="/opt/rtcds/userapps/release/vis/common/scripts/medm/overview/GRD_MINI.adl;SYSTEM={system}"
    }}
    '''.format(x=x,y=y,system=system)
    return txt,width,height


def sdf_mini(x,y,fec='123',subsys='ETMXT'):
    width = 260
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
    "composite file"="/opt/rtcds/userapps/release/vis/common/scripts/medm/overview/SDF_MINI.adl;FEC={fec},SUBSYS={subsys}"
    }}
    '''.format(x=x,y=y,fec=fec,subsys=subsys)
    return txt,width,height


if __name__=='__main__':
    systems = ['ETMX','ETMY']
    models = {'ETMX':[['ETMXT',68],['ETMXP',69],['ETMXMON',0],['MODALETMX',0]],
              'ETMY':[['ETMYT',65],['ETMYP',64],['ETMYMON',0],['MODALETMY',0]]}
    height = 200
    width = 18 
    contents = header    
    with open('./tmp.adl','w') as f:
        for system in systems:
            txt,w,h = grd_mini(x=width,y=height,system=system)
            contents += txt
            width += w+2 
            for model in models[system]:
                model,fec = model
                txt,w,h = sdf_mini(x=width,y=height,fec=fec,subsys=model)
                height += h+2
                contents += txt
            width -= w+2
            
        f.write(contents)
    
