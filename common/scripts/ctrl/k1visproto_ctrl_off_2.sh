#!/bin/sh

#Modified by A.Shoda 2015/6/12

#SET RAMP TIME
tdswrite K1:VIS-PROTO_F0_SERVOF_L_TRAMP 10.0
tdswrite K1:VIS-PROTO_F0_SERVOF_T_TRAMP 10.0
tdswrite K1:VIS-PROTO_F0_SERVOF_Y_TRAMP 10.0
tdswrite K1:VIS-PROTO_IM_SERVOF_L_TRAMP 5.0
tdswrite K1:VIS-PROTO_IM_SERVOF_T_TRAMP 5.0
tdswrite K1:VIS-PROTO_IM_SERVOF_V_TRAMP 5.0
tdswrite K1:VIS-PROTO_IM_SERVOF_R_TRAMP 5.0
tdswrite K1:VIS-PROTO_IM_SERVOF_P_TRAMP 5.0
tdswrite K1:VIS-PROTO_IM_SERVOF_Y_TRAMP 5.0
tdswrite K1:VIS-PROTO_TM_SERVOF_L_TRAMP 5.0
tdswrite K1:VIS-PROTO_TM_SERVOF_P_TRAMP 5.0
tdswrite K1:VIS-PROTO_TM_SERVOF_Y_TRAMP 5.0
tdswrite K1:VIS-PROTO_GAS_COILOUTF_F1_TRAMP 10.0
tdswrite K1:VIS-PROTO_GAS_COILOUTF_F2_TRAMP 10.0
tdswrite K1:VIS-PROTO_GAS_SERVOF_F0_TRAMP 10.0
tdswrite K1:VIS-PROTO_GAS_SERVOF_F1_TRAMP 10.0
tdswrite K1:VIS-PROTO_GAS_SERVOF_F2_TRAMP 10.0
#tdswrite K1:VIS-PROTO_F0_OPLEVF_Y_TRAMP 10.0
#tdswrite K1:VIS-PROTO_TM_OPLEVF_Y_TRAMP 10.0
#tdswrite K1:VIS-PROTO_TM_OPLEVF_P_TRAMP 10.0

#CLEAR HISTORY
#tdswrite K1:VIS-PROTO_F0_SERVOF_L_RSET 2
#tdswrite K1:VIS-PROTO_F0_SERVOF_T_RSET 2
#tdswrite K1:VIS-PROTO_F0_SERVOF_Y_RSET 2

#GAIN ON
tdswrite K1:VIS-PROTO_F0_SERVOF_L_GAIN 0.0
tdswrite K1:VIS-PROTO_F0_SERVOF_T_GAIN 0.0
tdswrite K1:VIS-PROTO_F0_SERVOF_Y_GAIN 0.0
tdswrite K1:VIS-PROTO_IM_SERVOF_L_GAIN 0.0
tdswrite K1:VIS-PROTO_IM_SERVOF_T_GAIN 0.0
tdswrite K1:VIS-PROTO_IM_SERVOF_V_GAIN 0.0
tdswrite K1:VIS-PROTO_IM_SERVOF_R_GAIN 0.0
tdswrite K1:VIS-PROTO_IM_SERVOF_P_GAIN 0.0
tdswrite K1:VIS-PROTO_IM_SERVOF_Y_GAIN 0.0
tdswrite K1:VIS-PROTO_TM_SERVOF_L_GAIN 0.0
tdswrite K1:VIS-PROTO_TM_SERVOF_P_GAIN 0.0
tdswrite K1:VIS-PROTO_TM_SERVOF_Y_GAIN 0.0
tdswrite K1:VIS-PROTO_GAS_SERVOF_F0_GAIN 0.0
tdswrite K1:VIS-PROTO_GAS_SERVOF_F1_GAIN 0.0
tdswrite K1:VIS-PROTO_GAS_SERVOF_F2_GAIN 0.0
#tdswrite K1:VIS-PROTO_F0_OPLEVF_Y_GAIN 0.0
#tdswrite K1:VIS-PROTO_TM_OPLEVF_Y_GAIN 0.0
#tdswrite K1:VIS-PROTO_TM_OPLEVF_P_GAIN 0.0

#BF OFFSET
#tdswrite K1:VIS-PROTO_GAS_COILOUTF_F2_SW1 8
#tdswrite K1:VIS-PROTO_GAS_COILOUTF_F1_SW1 8


