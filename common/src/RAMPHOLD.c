// Hold switch which can release the output with ramptime
// written by M. Nakano, 2020/04/01

void RAMPHOLD(double *argin, int nargin, double *argout, int nargout){
  /* Hold switch which can release the output with ramptime.
   * Note that several output need to be connected to the input with the unit delay
   *
   * INPUTS
   * argin[0] = Input
   * argin[1] = Hold flag
   * argin[2] = Ramp time
   * 
   * OUTPUTS
   * argout[0] = Output
   * argout[1] = Ramping flag
   * argout[2] = Holded value output
   * argout[3] = Input weight output
   * argout[4] = Holded value weight output
   * argout[5] = State ouptut
   */
  // Read inputs
  double Input = argin[0];
  int HoldFlag = argin[1];
  double RampTime = argin[2];
  double SampF = FE_RATE;
  static double HoldValue = 0;
  static double InputWeight = 1;
  static double HoldValWeight = 0;
  static int State = 0;
  static double OUTPUT = 0;
  
  double defRampTime = 3.;
  double defSampF = 16348.;
  
  /* define the incrementation step. Use default ramptime and sampling frequency when they are invalid */
  if(RampTime <= 0.0){
    RampTime = defRampTime;    
  }
  
  if (RampTime <= 0.0) {
    SampF = defSampF;
  }
  
  double IncVal = 1.0/RampTime/SampF;

  switch(State) {
  default:
  case 0: // In Normal State
    if (!!HoldFlag) { // If Triggered
      HoldValue = Input;
      InputWeight = 0.;
      HoldValWeight = 1.;
      State = 1;
    }
    break;

  case 1: // In Holded State
    if (!HoldFlag) {
      // If hold button disabled
      State = 2;
    }
    break;

  case 2: // In ramping state
    if (InputWeight >= 1.0) { // When ramp finished.
      HoldValue = 0;
      InputWeight = 1.;
      HoldValWeight = 0.;
      State = 0;
    }
    else if(!!HoldFlag) {
      HoldValue = OUTPUT;
      InputWeight = 0.;
      HoldValWeight = 1.;
      State = 1;
    }
    else {
      InputWeight = InputWeight + IncVal;
      HoldValWeight = HoldValWeight - IncVal;
    }
    break;
  }
  
  // Output
  OUTPUT = Input*InputWeight + HoldValue*HoldValWeight; 
  argout[0] = OUTPUT;
  argout[1] = (State == 2);
  argout[2] = HoldValue;
  argout[3] = InputWeight;
  argout[4] = HoldValWeight;
  argout[5] = State;

  return;

}

