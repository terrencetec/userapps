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
   * argin[3] = Sampling rate of the model
   * argin[4] = Holded Value input
   * argin[5] = Input weight input
   * argin[6] = Holded value weight input
   * argin[7] = State input
   * argin[8] = Output value of this block one tick before
   * 
   * OUTPUTS:
   * argout[0] = Output: need to be connected to argin[8] with unit delay
   * argout[1] = Ramping flag
   * argout[2] = Holded value output: need to be connected to argin[4] with unit delay
   * argout[3] = Input weight output: need to be connected to argin[5] with unit delay
   * argout[4] = Holded value weight output: need to be connected to argin[6] with unit delay
   * argout[5] = State ouptut: need to be connected to argin[7] with unit delay
   */

  // Read inputs
  double Input = argin[0];
  int HoldFlag = argin[1];
  double RampTime = argin[2];
  double SampF = argin[3];
  double HoldValue = argin[4];
  double InputWeight = argin[5];
  double HoldValWeight = argin[6];
  int State = argin[7];
  double BlockOutIn = argin[8];
  
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
      HoldValue = BlockOutIn;
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
  argout[0] = Input*InputWeight + HoldValue*HoldValWeight;
  argout[1] = (State == 2);
  argout[2] = HoldValue;
  argout[3] = InputWeight;
  argout[4] = HoldValWeight;
  argout[5] = State;

  return;

}

