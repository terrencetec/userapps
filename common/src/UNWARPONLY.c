// Simple atan function
// KK, JGP 8/18/2016
// modified 2017/2/14

void UNWARP (double *argin, int nargin, double *argout, int nargout){    

    double PCuphi = argin[0];
    double YCuphi = argin[1];
    double PDLphi = argin[2];
    double YDLphi = argin[3];
    double PF_Num = 0;
    double YF_Num = 0;
            
if( YCuphi - YDLphi < -4 ){
        YF_Num = YF_Num + 1;
        } else if (YCuphi- YDLphi >= 4)
        {
            YF_Num = YF_Num -1;
	 }


if( PCuphi - PDLphi < -4 ){
        PF_Num = PF_Num + 1;
        } else if (PCuphi- PDLphi >= 4)
        {
            PF_Num = PF_Num -1;
	 }
    
    argout[0] = PF_Num;
    argout[1] = YF_Num;
    
}


