#!/bin/sh

#TRAMP
tdswrite K1:VIS-PROTO_F0_BLEND_BLENDL_TRAMP 5.0
tdswrite K1:VIS-PROTO_F0_BLEND_BLENDT_TRAMP 5.0
tdswrite K1:VIS-PROTO_F0_BLEND_BLENDY_TRAMP 5.0

tdswrite K1:VIS-PROTO_F0_BLEND_BLENDL0_TRAMP 5.0
tdswrite K1:VIS-PROTO_F0_BLEND_BLENDT0_TRAMP 5.0
tdswrite K1:VIS-PROTO_F0_BLEND_BLENDY0_TRAMP 5.0


#SWITCH
tdswrite K1:VIS-PROTO_F0_BLEND_BLENDL_GAIN 0.0
tdswrite K1:VIS-PROTO_F0_BLEND_BLENDL0_GAIN 1.0

tdswrite K1:VIS-PROTO_F0_BLEND_BLENDT_GAIN 0.0
tdswrite K1:VIS-PROTO_F0_BLEND_BLENDT0_GAIN 1.0

tdswrite K1:VIS-PROTO_F0_BLEND_BLENDY_GAIN 0.0
tdswrite K1:VIS-PROTO_F0_BLEND_BLENDY0_GAIN 1.0

