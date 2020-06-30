// Simple atan function
// KK, JGP 8/18/2016
// modified 2017/2/20

void ARCTANDBL (double *argin, int nargin, double *argout, int nargout){    

    double YIsig = argin[0];
    double YQsig = argin[1];
    double YF_Num = argin[2];
    double YDLphi = argin[3];
    double YCuphi = 0;
    double PIsig = argin[4];
    double PQsig = argin[5];
    double PF_Num = argin[6];
    double PDLphi = argin[7];
    double PCuphi = 0;

YCuphi = latan2(YIsig,YQsig);
if( YCuphi - YDLphi < -4 ){
        YF_Num = YF_Num + 1;
        } else if (YCuphi- YDLphi >= 4)
        {
            YF_Num = YF_Num -1;
	 }

PCuphi = latan2(PIsig,PQsig);
if( PCuphi - PDLphi < -4 ){
        PF_Num = PF_Num + 1;
        } else if (PCuphi- PDLphi >= 4)
        {
            PF_Num = PF_Num -1;
	 }
    argout[0] = YF_Num * 2 * 3.14159 + YCuphi;
    argout[1] = YF_Num;
    argout[2] = YCuphi;

    argout[3] = PF_Num * 2 * 3.14159 + PCuphi;
    argout[4] = PF_Num;
    argout[5] = PCuphi;
}


