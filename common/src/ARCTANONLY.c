// Simple atan function
// KK, JGP 8/18/2016


void ARCTAN (double *argin, int nargin, double *argout, int nargout){    

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
    
    argout[0] = 2*latan2(Isig,Qsig);
    argout[1] = F_Num;
    argout[2] = Cuphi;
    

    
}


