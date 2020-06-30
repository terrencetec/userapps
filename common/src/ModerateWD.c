// Moderate WD shutdown script for VIS
// written by A. Shoda, 2019/5/9

void ModerateWD(double *argin, int nargin, double *argout, int nargout){
  /* Combining the WD information from the all stages, gradually increase
   * the BLOCK Flag from 0 to 1 in the provided ramp time when RESET 
   * bottun is activated.
   *
   * INPUTS
   * argin[0] = Combined WD Flag
   * argin[1] = Ramp time
   * argin[2] = Sampling rate of the model
   * 
   * OUTPUTS:
   * argout[0] = BLOCK Flag
   * argout[1] = STATE Bit Word
   * argout[2] = FIRSTTRIG Bit Word
   * argout[3] = CURRENTTRIG Bit Word
   * (1 = Sensor AC Tripped)
   */

  // Initialize
  static int state = 2;// state=2:blocked, state=1:ramped, state=0:OK 
  static int firstTrig = 0;
  static double IncWidth = 1.0/5/16348;// default ramp time 5 sec / 16 kHz

  static double blockFlag = 1;

  // Read inputs
  int WDFlags = argin[0];
  double RampInput = argin[1];
  double SampF = argin[2];

  int trig = (!!WDFlags); 

  switch(state) {
  case 0: // In Normal State
    if (trig) { // If Triggered
      firstTrig = trig;
      if (RampInput <= 0.0){
	IncWidth = 1.0/5/SampF; //Terrence changed 1 to 1.0 so its not performing integer division, which always gives 0 in this case.
      }
      else {
	IncWidth = 1.0/RampInput/SampF;
      }
      state = 1;
    }
    break;

  case 1: // In Ramped state
    if (blockFlag < 1) { // During increasing the flag
      blockFlag = blockFlag + IncWidth;
    }
    else { // If flag become 1
      blockFlag = 1;
      state = 2;
    }
    break;

  default:
  case 2: // In tripped state
    if (!trig) { // If reset buttom pressed
      blockFlag = 0;
      firstTrig = 0;
      state = 0;
    }
    break;
    
  }
  
  // Output
  argout[0] = blockFlag;
  argout[1] = state;
  argout[2] = firstTrig;
  argout[3] = trig;

  return;

}

