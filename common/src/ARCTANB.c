// Simple atan function
// KK, JGP 8/18/2016


void ARCTANB (double *argin, int nargin, double *argout, int nargout){    

    double Isig = argin[0];
    double Qsig = argin[1];
    double F_Num = argin[2];
    double DLphi = argin[3];
    double Cuphi = 0;
Cuphi = latan2(Isig,Qsig);
if( Cuphi - DLphi < -4 ){
        F_Num = F_Num + 1;
        } else if (Cuphi- DLphi >= 4)
        {
            F_Num = F_Num -1;
	 }
    
    argout[0] = F_Num * 2 * 4 * latan2(1,1) + Cuphi;
    argout[1] = F_Num;
    argout[2] = Cuphi;
}


