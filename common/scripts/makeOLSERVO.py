#!/usr/bin/env python

file = open('VIS.adl', 'w')
header = '''
file {
	name="OFS_COMP.adl"
	version=030107
}
display {
	object {
		x=2712
		y=455
		width=1021
		height=300
	}
	clr=14
	bclr=4
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
jj = 0
file.write(header)
for ii in range(31,-32,-1):
    if ii >= 0:
        box = '''
"text entry" {
	object {
		x=''' + str(75+jj/8*125) + '''
		y=''' + str(40+(jj-(jj/8)*8)*30) + '''
		width=50
		height=25
	}
	control {
		chan="$(IFO):$(MODEL)-$(CHANNEL)_GAIN''' + str(ii) + '''_OFS"
		clr=14
		bclr=4
	}
	limits {
	}
}
text {
	object {
		x=''' + str(20+jj/8*125) + '''
		y=''' + str(40+(jj-(jj/8)*8)*30) + '''
		width=69
		height=20
	}
	"basic attribute" {
		clr=14
	}
	textix="GAIN''' + str(ii) + '''"
}

'''
    else:
   
        box = '''
"text entry" {
	object {
		x=''' + str(75+jj/8*125) + '''
		y=''' + str(40+(jj-(jj/8)*8)*30) + '''
		width=50
		height=25
	}
	control {
		chan="$(IFO):$(MODEL)-$(CHANNEL)_GAINNEG''' + str(-ii) + '''_OFS"
		clr=14
		bclr=4
	}
	limits {
	}
}
text {
	object {
		x=''' + str(20+jj/8*125) + '''
		y=''' + str(40+(jj-(jj/8)*8)*30) + '''
		width=69
		height=20
	}
	"basic attribute" {
		clr=14
	}
	textix="GAIN''' + str(ii) + '''"
}

'''
    file.write(box)
    jj = jj+1
file.close()
