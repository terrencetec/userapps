/*
 *  WATCHDOG.c
 *  Contains 4 functions that serve as state machines for the suspension watchdogs. 
 *  Each of the four states are descibed in the comments below each function.
 *  
 *  Written by Jeff Kissel
 *  May 2011
 *  Modified by Koji Arai for AC/DC OSEM Sensor Flags
 *  Aug 2011
 *  $Id$
 */

////////////////////////////////////////////////
//////////// START OSEMWATCHDOG ////////////////
////////////////////////////////////////////////

void OSEMWATCHDOG(double *argin, int nargin, double *argout, int nargout) {
  /*  State machine for ALL SUS types; possible signals on which to trigger 
   *  has been reduced to the AC BLRMS of OSEMs, as per ECR E1400102, to 
   *  reduce false alarm rates. 
   *  Receives watchdog flags and outputs state changes and status
   * 
   *  INPUTS
   *  argin[0] = RESET Flag
   *  argin[1] = OSEM Sensor AC Flag
   *
   *  OUTPUTS:
   *  argout[0] = BLOCK Flag
   *  argout[1] = STATE Bit Word
   *  argout[2] = FIRSTTRIG Bit Word (indicating which flag tripped the watchdog)
   *  argout[3] = CURRENTTRIG Bit Word (indication flags which are still triggering)
   *
   *  The FIRSTTRIG and CURRENTTRIG Bit Words contain the following information
   *  (1 = OSEM AC Sensor Tripped)
   */

  // Initialize
  static int state           = 2;             // Start in STATE 2 (TRIGGERED)
  static int firstTrigger    = 0;             // Start with no indication of triggers

  int blockFlag              = 1;             // Start script BLOCKED state

  // Read inputs
  int resetFlag	      = argin[0];            // Reset Flag
  int sensACTriggered = argin[1];            // Sensor AC Flag
  
  // Check for triggers - make a 1 character bitfield so we can tell which triggers triggered
  // The !! (double inverse) syntax guarantees that the given value is 0 or 1.
  // The << is a bitwise shift left, i.e. 1 << 2 == 4 and 1 << 3 == 8.
  // So, if the actuators trigger, triggers = 100 (bininary);
  // int triggers = (!!sensDCTriggered ) | (!!sensACTriggered << 1) | (!!actsTriggered << 2);

  // Because only one trigger type remains, bitwise shift left is no longer necessary
  // but it's cool, so I leave in in the notes above in case we ever need it again.
  int triggers = (!!sensACTriggered);

  // State transitions
  switch (state) {
  case 1: // To STATE 1 (ARMED)
    if (triggers) {
      firstTrigger = triggers; // Record the trigger bit word after the first trigger
      state = 2;
    }
    break;
    
  default:
  case 2: // To STATE 2 (TRIGGERED)
    if (!triggers && resetFlag) {
      firstTrigger = 0; // Reset first trigger
      state = 1;
    }
    break;
  }
 
  // State actions
  switch (state) {
  case 1: // STATE 1 (ARMED)
    blockFlag = 0;     // Leave actuation path open
    break;
    
  default:
  case 2: // STATE 2 (TRIGGERED)
    blockFlag = 1;     // Block actuation path
    break;
    
  }

  // Output
  argout[0] = blockFlag;
  argout[1] = state;
  argout[2] = firstTrigger;
  argout[3] = triggers;

  return;
}
////////////////////////////////////////////////
////////////// END OSEMWATCHDOG ////////////////
////////////////////////////////////////////////


////////////////////////////////////////////////
//////////// START QUADESDWATCHDOG /////////////
////////////////////////////////////////////////

void QUADESDWATCHDOG(double *argin, int nargin, double *argout, int nargout) {
  /*  State machine for QUAD L3 stage
   *  Receives watchdog flags and outputs state changes and status
   * 
   *  INPUTS
   *  argin[0] = RESET Flag
   *  argin[1] = Optical Lever SUM Flag
   *  argin[2] = Optical Lever Pitch/Yaw Flag
   *  argin[3] = ESD Quadrant Flag
   *  argin[4] = ESD Bias Flag
   *
   *  OUTPUTS:
   *  argout[0] = BLOCK Flag
   *  argout[1] = STATE Bit Word
   *  argout[2] = FIRSTTRIG Bit Word (indicating which flag tripped the watchdog)
   *  argout[3] = CURRENTTRIG Bit Word (indication flags which are still triggering)
   *
   *  The FIRSTTRIG and CURRENTTRIG Bit Words contain the following information
   *  (1 = OPLEV SUM Tripped; 2 = OPLEV P/Y Tripped; 4 = ESD QDRNT Tripped; 8 = ESD BIAS Tripped)
   */

  // Initialize
  static int state           = 2;             // Start in STATE 2 (TRIGGERED)
  static int firstTrigger    = 0;             // Start with no indication of triggers

  int blockFlag              = 1;             // Start script BLOCKED state

  // Read inputs
  int resetFlag	       = argin[0];        // Reset Flag
  int olsumTriggered   = argin[1];        // Optical Lever SUM  Flag   
  int oplevTriggered   = argin[2];        // Optical Lever Pitch/Yaw Flag
  int qdrntsTriggered  = argin[3];        // ESD Quadrant Flag
  int biasTriggered    = argin[4];        // ESD Bias Flag
  
  // Check for triggers - make a 4 character bitfield so we can tell which triggers triggered
  // The !! (double inverse) syntax guarantees that the given value is 0 or 1.
  // The << is a bitwise shift left, i.e. 1 << 2 == 4 and 1 << 3 == 8.
  // So, if the optical lever P/Y and ESD bias triggers = 1010;
  int triggers = (!!olsumTriggered) | (!!oplevTriggered << 1) | (!!qdrntsTriggered << 2) | (!!biasTriggered << 3);

  // State transitions
  switch (state) {
  case 1: // To STATE 1 (ARMED)
    if (triggers) {
      firstTrigger = triggers; // Record the trigger bit word after the first trigger
      state = 2;
    }
    break;
    
  default:
  case 2: // To STATE 2 (TRIGGERED)
    if (!triggers && resetFlag) {
      firstTrigger = 0; // Reset first trigger
      state = 1;
    }
    break;
  }
 
  // State actions
  switch (state) {
  case 1: // STATE 1 (ARMED)
    blockFlag = 0;     // Leave actuation path open
    break;
    
  default:
  case 2: // STATE 2 (TRIGGERED)
    blockFlag = 1;     // Block actuation path
    break;
    
  }

  // Output
  argout[0] = blockFlag;
  argout[1] = state;
  argout[2] = firstTrigger;
  argout[3] = triggers;

  return;
}
////////////////////////////////////////////////
///////////// END QUADESDWATCHDOG //////////////
////////////////////////////////////////////////


////////////////////////////////////////////////
//////////// START OSOPWATCHDOG /////////////
////////////////////////////////////////////////

void OSOPWATCHDOG(double *argin, int nargin, double *argout, int nargout) {
  /*  State machine for HLTS M3 stage (contains both OSEMs and OpLevs)
   *  Receives watchdog flags and outputs state changes and status
   * 
   *  INPUTS
   *  argin[0] = RESET Flag
   *  argin[1] = Optical Lever SUM Flag
   *  argin[2] = Optical Lever Pitch/Yaw Flag
   *  argin[3] = OSEM Sensor DC Flag 
   *  argin[4] = OSEM Sensor AC Flag
   *  argin[5] = Coil Actuator Flag
   *
   *  OUTPUTS:
   *  argout[0] = BLOCK Flag
   *  argout[1] = STATE Bit Word
   *  argout[2] = FIRSTTRIG Bit Word (indicating which flag tripped the watchdog)
   *  argout[3] = CURRENTTRIG Bit Word (indication flags which are still triggering)
   *
   *  The FIRSTTRIG and CURRENTTRIG Bit Words contain the following information
   *  (1 = OPLEV SUM Tripped; 2 = OPLEV P/Y Tripped; 4 = OSEM DC Flag Tripped; 8 = OSEM AC Flag Tripped 16 = Coil ACT Flag Tripped)
   */

  // Initialize
  static int state           = 2;             // Start in STATE 2 (TRIGGERED)
  static int firstTrigger    = 0;             // Start with no indication of triggers

  int blockFlag              = 1;             // Start script BLOCKED state

  // Read inputs
  int resetFlag	       = argin[0];        // Reset Flag
  int sensDCTriggered  = argin[1];        // Sensor DC Flag
  int sensACTriggered  = argin[2];        // Sensor AC Flag
  int olsumTriggered   = argin[3];        // Optical Lever SUM  Flag   
  int oplevTriggered   = argin[4];        // Optical Lever Pitch/Yaw Flag
  int coilTriggered    = argin[5];        // Actuator Flag 

  // Check for triggers - make a 5 character bitfield so we can tell which triggers triggered
  // The !! (double inverse) syntax guarantees that the given value is 0 or 1.
  // The << is a bitwise shift left, i.e. 1 << 2 == 4 and 1 << 3 == 8.
  // So, if the optical lever P/Y and actuator coir triggers = 10010.
  int triggers = (!!sensDCTriggered) | (!!sensACTriggered << 1) | (!!olsumTriggered << 2) | (!!oplevTriggered << 3) | (!!coilTriggered << 4);

  // State transitions
  switch (state) {
  case 1: // To STATE 1 (ARMED)
    if (triggers) {
      firstTrigger = triggers; // Record the trigger bit word after the first trigger
      state = 2;
    }
    break;
    
  default:
  case 2: // To STATE 2 (TRIGGERED)
    if (!triggers && resetFlag) {
      firstTrigger = 0; // Reset first trigger
      state = 1;
    }
    break;
  }
 
  // State actions
  switch (state) {
  case 1: // STATE 1 (ARMED)
    blockFlag = 0;     // Leave actuation path open
    break;
    
  default:
  case 2: // STATE 2 (TRIGGERED)
    blockFlag = 1;     // Block actuation path
    break;
    
  }

  // Output
  argout[0] = blockFlag;
  argout[1] = state;
  argout[2] = firstTrigger;
  argout[3] = triggers;

  return;
}
////////////////////////////////////////////////
///////////// END OSOPWATCHDOG/////////////
////////////////////////////////////////////////


////////////////////////////////////////////////
//////////// START OPLEVWATCHDOG ///////////////
////////////////////////////////////////////////

void OPLEVWATCHDOG(double *argin, int nargin, double *argout, int nargout) {
  /*  State machine for BSFM M3 (contains only OpLevs)
   *  Receives watchdog flags and outputs state changes and status
   * 
   *  INPUTS
   *  argin[0] = RESET Flag
   *  argin[1] = Optical Lever SUM Flag
   *  argin[2] = Optical Lever Pitch/Yaw Flag
   *
   *  OUTPUTS:
   *  argout[0] = BLOCK Flag
   *  argout[1] = STATE Bit Word
   *  argout[2] = FIRSTTRIG Bit Word (indicating which flag tripped the watchdog)
   *  argout[3] = CURRENTTRIG Bit Word (indication flags which are still triggering)
   *
   *  The FIRSTTRIG and CURRENTTRIG Bit Words contain the following information
   *  (1 = OPLEV SUM Tripped; 2 = OPLEV P/Y Tripped)
   */

  // Initialize
  static int state           = 2;             // Start in STATE 2 (TRIGGERED)
  static int firstTrigger    = 0;             // Start with no indication of triggers

  int blockFlag              = 1;             // Start script BLOCKED state

  // Read inputs
  int resetFlag	       = argin[0];        // Reset Flag
  int olsumTriggered   = argin[1];        // Optical Lever SUM  Flag   
  int oplevTriggered   = argin[2];        // Optical Lever Pitch/Yaw Flag

  // Check for triggers - make a 5 character bitfield so we can tell which triggers triggered
  // The !! (double inverse) syntax guarantees that the given value is 0 or 1.
  // The << is a bitwise shift left, i.e. 1 << 2 == 4 and 1 << 3 == 8.
  // So, optical lever P/Y trip = 10, optical lever SUM = 01.
  int triggers = (!!olsumTriggered) | (!!oplevTriggered << 1);

  // State transitions
  switch (state) {
  case 1: // To STATE 1 (ARMED)
    if (triggers) {
      firstTrigger = triggers; // Record the trigger bit word after the first trigger
      state = 2;
    }
    break;
    
  default:
  case 2: // To STATE 2 (TRIGGERED)
    if (!triggers && resetFlag) {
      firstTrigger = 0; // Reset first trigger
      state = 1;
    }
    break;
  }
 
  // State actions
  switch (state) {
  case 1: // STATE 1 (ARMED)
    blockFlag = 0;     // Leave actuation path open
    break;
    
  default:
  case 2: // STATE 2 (TRIGGERED)
    blockFlag = 1;     // Block actuation path
    break;
    
  }

  // Output
  argout[0] = blockFlag;
  argout[1] = state;
  argout[2] = firstTrigger;
  argout[3] = triggers;

  return;
}
////////////////////////////////////////////////
///////////// END OPLEVWATCHDOG ////////////////
////////////////////////////////////////////////


