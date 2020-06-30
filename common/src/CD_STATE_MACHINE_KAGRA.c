/*
 * CD_STATE_MACHINE.c
 * JCB Oct 4, 2011
 *
 * CD_STATE_MACHINE is a compilation of state machines for setting the 
 * binary output of the coil drivers for the suspensions so as to match
 * the digital simulated anti-imaging filters states to the opposite of
 * the analog anti-imaging filter states.
 * 
 * Functions are:
 * PUM
 * TOP
 * TACQ
 * TACQ_M2
 * UIM
 * SINGLE
 *
 * INPUTS:
 * argin[0] = coilTestEnable
 * argin[1] = epicsStateRequest 
 * argin[2] = iscRequest 
 * argin[3] = msDelayTurnOn 
 * argin[4] = msDelayTurnOff
 * PUM ONLY: argin[5] = analogRmsWdReset
 *
 * OUTPUTS:
 * argout[0] = digital filter mask bits 
 * argout[1] = digital filter control bits 
 * argout[2] = binary output control bits 
 */



//PUM - handles the 4 OSEM Penultimate Mass stages for QUADs

// Digital Anti AcqOn, Anti AcqOff, Anti Low Pass are always ON

//  STATE 1 => Analog Acq OFF, Low Pass OFF
//		Digital Sim AcqOff ON, Sim AcqOn OFF, Sim Low Pass ON
//  STATE 2 => Analog Acq On, Low Pass OFF
//              Digital Sim AcqOff OFF, Sim AcqOn ON, Sim Low Pass ON
//  STATE 3 => Analog Acq OFF, Low Pass ON
//              Digital Sim AcqOff ON, Sim AcqOn OFF, Sim Low Pass OFF
//  STATE 4 => Analog Acq ON, Low Pass ON
//              Digital Sim AcqOff OFF, Sim AcqOn ON, Sim Low Pass OFF

//Takes 6 inputs:
//COIL / TEST ENABLE (0 for Coil or 1 for Test)
//EPICS state request (0 hands control to ISC fast request)
//ISC Fast state request
//Turn On Delay (How many ms to wait before switching digital filters when analog filters are turning on)
//Turn Off Delay (How many ms to wait before switching digital filters when analog filters are turning off)
//PUM Analog RMS Watchdog Momentary Reset

//Provides 3 outputs:
//argout[0] is Mask bit for Filter module
//argout[1] is Control bit for Filter module
//argout[2] is control bits for BO card
//          1st bit (1) (rightmost) is Low Pass On/Off
//          2nd bit (2) is PUM Analog RMS Watchdog Momentary reset 
//          3rd bit (4) is Acquire On/Off
//          4th bit (8) is Test Coil Enable


void PUM(double *argin, int nargin, double *argout, int nargout) {
  
  // Analog filter switching delay -> Cycles to wait before sending command to digital filters
  static long cycleCounter = 0;
  // Last state we finished going to
  static int state = 1;  
  // State we've been requested to go to
  static int request = 1;

  // Initialize control bit variables
  int analog_control_bits = 0b0;
  int initial_analog_control_bits = 0b0;
  int digital_control_bits;
  int digital_mask_bits = 0b0;
  int digital_turn_on_mask = 0b0;
  int digital_stay_the_same_mask = 0b0;
  int analog_to_digital_control[3][2];
  int mask_user_override = 0;

  int analog_bit;

  // Set always on digital control bits
  digital_control_bits = 0b0011100000;

  // Set up digital filter state depending on analog filter state
  analog_to_digital_control[2][0] = 0b0000000010; //Analog LP filter Off
  analog_to_digital_control[2][1] = 0b0000000001; //Analog LP filter On
  analog_to_digital_control[1][0] = 0b0000000000; //Readback, so no control
  analog_to_digital_control[1][1] = 0b0000000000; //Readback, so no control
  analog_to_digital_control[0][0] = 0b0000000100; //Analog Acquire filter Off
  analog_to_digital_control[0][1] = 0b0000000000; //Analog Acquire filter On

  // Read inputs
  int coilTestEnable     = argin[0]; //0 => Digital control for Coil driver, 1 => use Test Analog in
  int epicsStateRequest   = argin[1]; //State request from Epics
  int iscRequest     = argin[2]; // State request from isc
  // Epics input indicating how long to delay digital filter switching in ms when Analog filters are turning ON 
  double msDelayTurnOn = argin[3];
  // Epics input indicating how long to delay digital filter switching in ms when Analog filters are turning OFF 
  double msDelayTurnOff =argin[4];
  int analogRmsWdReset = argin[5]; //Request to reset analog RMS watchdog
  
  // Cycles to delay before switching digital filters
  long cycleDelayTurnOn = msDelayTurnOn * FE_RATE / 1000;  //Used when analog filters turning on
  long cycleDelayTurnOff = msDelayTurnOff * FE_RATE /1000;  //Used when analog filters turning off
  

  // If we're not already changing states, go ahead and check
  if (cycleCounter == 0) {
    // Epics state 0 => use ISC request
    if (epicsStateRequest == 0) {
      request = iscRequest;
    } else {
      request = epicsStateRequest;
      // Set an a manual override, so user can control digital filters
      // Only affects the mask bits
      if (epicsStateRequest < 0) {
        mask_user_override = 1;
        request = -epicsStateRequest;
      }
    }
  }
  
  

  //If request is not equal to state, then we are changing states and need to count
  if (request != state) {
    cycleCounter++;
    //We've waited for cycleDelay, now finish the transition to request from state
    if ((cycleCounter > cycleDelayTurnOn) && (cycleCounter > cycleDelayTurnOff)) {
      cycleCounter = 0;
      state = request;
    }
  }

  // Request transitions (handles analog switching)
  // 2nd bit is for analog watchdog momentary reset - handled later
  switch (request) {
  case 1: // To STATE 1
    analog_control_bits = 0b000; // LP Off (1st 0), Acq Off (3rd 0)
    break;
  case 2: // To STATE 2
    analog_control_bits = 0b100; //LP Off (1st 0), Acq On (3rd 1)
    break;
  case 3:
    analog_control_bits = 0b001; // LP On (1st 1), Acq Off (3rd 0)
    break;
  case 4:
    analog_control_bits = 0b101; // LP On (1st 1), Acq On (3rd 1)
    break;
  default:  //Default state - everything off
    analog_control_bits = 0b000;
    break;    
	}
  // If cycleCounter = 0, then we are not changing states
  // Base the digital filters choices on the request analog bits (request == state in this case)
  if (cycleCounter == 0) {
     for (analog_bit=0 ; analog_bit < 3 ; analog_bit++ ) {
       if (0b1 & (analog_control_bits >> analog_bit)) {
         digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
       } else {
         digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
       }
     }
  // Handle the case where were changing states
  } else {
 
    // Prior state control bit (used to determine if an analog filter is turning on or off)
    // 2nd bit is not used - represent Reset Monitor bit - but there's a single reset for entire board
    switch (state) {
    case 1: // To STATE 1
      initial_analog_control_bits = 0b000; // LP Off (1st 0), Acq Off (3rd 0)
      break;
    case 2: // To STATE 2
      initial_analog_control_bits = 0b100; //LP Off (1st 0), Acq On (3rd 1)
      break;
    case 3:
      initial_analog_control_bits = 0b001; // LP On (1st 1), Acq Off (3rd 0)
      break;
    case 4:
      initial_analog_control_bits = 0b101; // LP On (1st 1), Acq On (3rd 1)
      break;
    default:  //Default state - everything off
      initial_analog_control_bits = 0b000;
      break;
          }

    // Determine if an analog filter is turning on versus turning off or staying the same
    // 1 indicates that case applies (turn on, turn off, or stay the same)
    digital_turn_on_mask =  (~(initial_analog_control_bits) & analog_control_bits);
    digital_stay_the_same_mask = ~(initial_analog_control_bits ^ analog_control_bits);
  
    // Cycle through all the analog bits
    // Determine if the analog bits are staying the same
    // If so, keep the associated digital filters in the same state
    // If the analog bits are turning on, determine if we've waited long enough, 
    // then change the associated digital filters to the on state.  Otherwise, keep them in the off state.
    // If the analog bits are turning off, determine if we've waited long enough,
    // then change the associated digital filters to the off state.  Otherwise, keep them in the on state.
    for (analog_bit=0 ; analog_bit < 3 ; analog_bit++ ) {
        if (0b1 & (digital_stay_the_same_mask >> analog_bit)) {
          if (0b1 & (analog_control_bits >> analog_bit)) {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
          } else {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
          }
        } else if ( 0b1 & (digital_turn_on_mask >> analog_bit)) {
          if (cycleCounter > cycleDelayTurnOn) {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
        	} else {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
        	}
        } else {
          if (cycleCounter > cycleDelayTurnOff) {
  	  digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
          } else {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
          }
        }
      }
  }  // Finished with the case where states are changing
  
  //Set digital_mask_bits, used by Filter module to determine which filters are under front end control
  //Simple for now - in principle could be made more specific like the above digital control bits and placed
  //inside the state transition codea
  if (mask_user_override == 0) {
    digital_mask_bits = 0b0011100111;
  } else {
    digital_mask_bits = 0b0000000000;
  }

  //If coil enabled, need to turn 4th bit on (add 8)
  if (coilTestEnable == 1) {
    analog_control_bits = analog_control_bits + 8; //Analog filter control bits
  }

  //If reset analog RMS Watchdog set high, turn on 2nd bit (add 2)
  if (analogRmsWdReset == 1) {
    analog_control_bits = analog_control_bits + 2; //Analog filter control bits
  }

  //Send out the calculated bits
  argout[0] = (double) digital_mask_bits;
  argout[1] = (double) digital_control_bits;
  argout[2] = (double) analog_control_bits;
  return;
}



//TOP - handles the 6 OSEM top stages for QUADs, HXTS, BSFM, HAUX,TMTS, OMCS

// Digital Anti Acq, Anti Low Pass are always ON

//  STATE 1 =>  Analog Low Pass OFF
//		Sim Low Pass ON
//  STATE 2 =>  Analog Low Pass OFF
//              Sim Low Pass OFF 

//Takes 5 inputs:
//COIL / TEST ENABLE (0 for Coil or 1 for Test)
//EPICS state request (0 hands control to ISC fast request)
//ISC Fast state request0
//Turn On Delay (How many ms to wait before switching digital filters when analog filters are turning on)
//Turn Off Delay (How many ms to wait before switching digital filters when analog filters are turning off)

//Provides 3 outputs:
//argout[0] is Mask bit for Filter module
//argout[1] is Control bit for Filter module
//argout[2] is control bits for BO card
//          1st bit (1) (rightmost) is Low Pass On/Off 
//          2nd bit (2) is Test Coil Enable


void TOP(double *argin, int nargin, double *argout, int nargout) {
  
  // Analog filter switching delay -> Cycles to wait before sending command to digital filters
  static long cycleCounter = 0;
  //Last state we finished going to
  static int state = 1;  
  //State we've been requested to go to
  static int request = 1;

  //Initialize control bit variables

  int analog_control_bits = 0b0;
  int initial_analog_control_bits = 0b0;
  int digital_control_bits;
  int digital_mask_bits = 0b0;
  int digital_turn_on_mask = 0b0; 
  int digital_stay_the_same_mask = 0b0;
  int analog_to_digital_control[1][2];
  int mask_user_override = 0;

  int analog_bit;

  // Set always on digital control bits
  digital_control_bits = 0b0001100000;

  // Set up digital filter state depending on analog filter state
  analog_to_digital_control[0][0] = 0b0000000010; //Analog LP filter Off
  analog_to_digital_control[0][1] = 0b0000000000; //Analog LP filter On

  // Read inputs
  int coilTestEnable     = argin[0]; //0 => Digital control for Coil driver, 1 => use Test Analog in
  int epicsStateRequest   = argin[1]; //State request from Epics
  int iscRequest     = argin[2]; // State request from isc
  // Epics input indicating how long to delay digital filter switching in ms when Analog filters are turning ON 
  double msDelayTurnOn = argin[3];
  // Epics input indicating how long to delay digital filter switching in ms when Analog filters are turning OFF 
  double msDelayTurnOff =argin[4];
  int analogRmsWdReset = argin[5]; //Request to reset analog RMS watchdog
  
  // Cycles to delay before switching digital filters
  long cycleDelayTurnOn = msDelayTurnOn * FE_RATE / 1000;  //Used when analog filters turning on
  long cycleDelayTurnOff = msDelayTurnOff * FE_RATE /1000;  //Used when analog filters turning off

  //If we're not already changing states, go ahead and check
  if (cycleCounter == 0) {
    // Epics state 0 => use ISC request
    if (epicsStateRequest == 0) {
      request = iscRequest;
    } else {
      request = epicsStateRequest;
      // Set an a manual override, so user can control digital filters
      // Only affects the mask bits
      if (epicsStateRequest < 0) {
        mask_user_override = 1;
        request = -epicsStateRequest;
      }
    }
  }
  
  //If request is not equal to state, then we are changing states and need to count
  if (request != state) {
    cycleCounter++;
    //We've waited for cycleDelay, now finish the transition to request from state
    if ((cycleCounter > cycleDelayTurnOn) && (cycleCounter > cycleDelayTurnOff)) {
      cycleCounter = 0;
      state = request;
    }
  }


  // Request transitions (handles analog switching)
  switch (request) {
  case 1: // To STATE 1
    analog_control_bits = 0b0; // LP Off (0)
    break;
  case 2: // To STATE 2
    analog_control_bits = 0b1; //LP ON (1)
    break;
  default:  //Default state - everything off
    analog_control_bits = 0b0;
    break;    
	}

  // If cycleCounter = 0, then we are not changing states
  // Base the digital filters choices on the request analog bits (request == state in this case)
  if (cycleCounter == 0) {
     for (analog_bit=0 ; analog_bit < 1 ; analog_bit++ ) {
       if (0b1 & (analog_control_bits >> analog_bit)) {
         digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
       } else {
         digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
       }
     }
  // Handle the case where were changing states
  } else {

    // Prior state control bit (used to determine if an analog filter is turning on or off)
    switch (state) {
    case 1: // To STATE 1
      initial_analog_control_bits = 0b0; // LP Off (0)
      break;
    case 2: // To STATE 2
      initial_analog_control_bits = 0b1; //LP ON (1)
      break;
    default:  //Default state - everything off
      initial_analog_control_bits = 0b0;
      break;
          }

    // Determine if an analog filter is turning on versus turning off or staying the same
    // 1 indicates that case applies (turn on, turn off, or stay the same)
    digital_turn_on_mask =  (~(initial_analog_control_bits) & analog_control_bits);
    digital_stay_the_same_mask = ~(initial_analog_control_bits ^ analog_control_bits);
  
    // Cycle through all the analog bits
    // Determine if the analog bits are staying the same
    // If so, keep the associated digital filters in the same state
    // If the analog bits are turning on, determine if we've waited long enough, 
    // then change the associated digital filters to the on state.  Otherwise, keep them in the off state.
    // If the analog bits are turning off, determine if we've waited long enough,
    // then change the associated digital filters to the off state.  Otherwise, keep them in the on state.
    for (analog_bit=0 ; analog_bit < 1 ; analog_bit++ ) {
        if (0b1 & (digital_stay_the_same_mask >> analog_bit)) {
          if (0b1 & (analog_control_bits >> analog_bit)) {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
          } else {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
          }
        } else if ( 0b1 & (digital_turn_on_mask >> analog_bit)) {
          if (cycleCounter > cycleDelayTurnOn) {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
        	} else {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
        	}
        } else {
          if (cycleCounter > cycleDelayTurnOff) {
  	  digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
          } else {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
          }
        }
      }
  }  // Finished with the case where states are changing

  //Set digital_mask_bits, used by Filter module to determine which filters are under front end control
  //Simple for now - in principle could be made more specific like the above digital control bits and placed
  //inside the state transition code

  if (mask_user_override == 0) {
    digital_mask_bits = 0b0011100111;
  } else {
    digital_mask_bits = 0b0000000000;
  }


  //If coil enabled, need to turn 2nd bit on (add 2)
  if (coilTestEnable == 1) {
    analog_control_bits = analog_control_bits + 2; //Analog filter control bits
  }

  //Send out the calculated bits
  argout[0] = (double) digital_mask_bits;
  argout[1] = (double) digital_control_bits;
  argout[2] = (double) analog_control_bits;
  return;
}

//TACQ_M2 - handles the Mass 2 4 OSEM stage for the HSTS mode cleaner 

// Digital Anti AcqOn, Anti AcqOff, Anti Low Pass are always ON

//  STATE 1 => Analog Acq OFF, Low Pass OFF
//		Digital Sim AcqOff ON, Sim AcqOn OFF, Sim Low Pass ON
//  STATE 2 => Analog Acq On, Low Pass OFF
//              Digital Sim AcqOff OFF, Sim AcqOn ON, Sim Low Pass ON
//  STATE 3 => Analog Acq OFF, Low Pass ON
//              Digital Sim AcqOff ON, Sim AcqOn OFF, Sim Low Pass OFF
//  STATE 4 => Analog Acq ON, Low Pass ON
//              Digital Sim AcqOff OFF, Sim AcqOn ON, Sim Low Pass OFF

//Takes 5 inputs:
//COIL / TEST ENABLE (0 for Coil or 1 for Test)
//EPICS state request (0 hands control to ISC fast request)
//ISC Fast state request
//Turn On Delay (How many ms to wait before switching digital filters when analog filters are turning on)
//Turn Off Delay (How many ms to wait before switching digital filters when analog filters are turning off)


//Provides 3 outputs:
//argout[0] is Mask bit for Filter module
//argout[1] is Control bit for Filter module
//argout[2] is control bits for BO card
//          1st bit (1) (rightmost) is Low Pass On/Off
//          2nd bit (2) is Acquire On/Off
//          3rd bit (4) is Test Coil Enable


void TACQ_M2(double *argin, int nargin, double *argout, int nargout) {
  
  // Analog filter switching delay -> Cycles to wait before sending command to digital filters
  static long cycleCounter = 0;
  //Last state we finished going to
  static int state = 1;  
  //State we've been requested to go to
  static int request = 1;

  //initialize control bit variables
  int analog_control_bits = 0b0;
  int initial_analog_control_bits = 0b0;
  int digital_control_bits;
  int digital_mask_bits = 0b0;
  int digital_turn_on_mask = 0b0; 
  int digital_stay_the_same_mask = 0b0;
  int analog_to_digital_control[2][2];
  int mask_user_override = 0;

  int analog_bit;

  // Set always on digital control bits
  digital_control_bits = 0b0001100000;

  // Set up digital filter state depending on analog filter state
  analog_to_digital_control[1][0] = 0b0000000001; //Analog Acquire filter Off
  analog_to_digital_control[1][1] = 0b0000000000; //Analog Acquire filter On
  analog_to_digital_control[0][0] = 0b0000000010; //Analog LP filter Off
  analog_to_digital_control[0][1] = 0b0000000000; //Analog LP filter On


  // Read inputs
  int coilTestEnable     = argin[0]; //0 => Digital control for Coil driver, 1 => use Test Analog in
  int epicsStateRequest   = argin[1]; //State request from Epics
  int iscRequest     = argin[2]; // State request from isc
  // Epics input indicating how long to delay digital filter switching in ms when Analog filters are turning ON 
  double msDelayTurnOn = argin[3];
  // Epics input indicating how long to delay digital filter switching in ms when Analog filters are turning OFF 
  double msDelayTurnOff =argin[4];

  // Cycles to delay before switching digital filters
  long cycleDelayTurnOn = msDelayTurnOn * FE_RATE / 1000;  //Used when analog filters turning on
  long cycleDelayTurnOff = msDelayTurnOff * FE_RATE /1000;  //Used when analog filters turning off

  //If we're not already changing states, go ahead and check
  if (cycleCounter == 0) {
    // Epics state 0 => use ISC request
    if (epicsStateRequest == 0) {
      request = iscRequest;
    } else {
      request = epicsStateRequest;
      // Set an a manual override, so user can control digital filters
      // Only affects the mask bits
      if (epicsStateRequest < 0) {
        mask_user_override = 1;
        request = -epicsStateRequest;
      }
    }
  }
  
  //If request is not equal to state, then we are changing states and need to count
  if (request != state) {
    cycleCounter++;
    //We've waited for cycleDelay, now finish the transition to request from state
    if ((cycleCounter > cycleDelayTurnOn) && (cycleCounter > cycleDelayTurnOff)) {
      cycleCounter = 0;
      state = request;
    }
  }


  // Request transitions (handles analog switching)
  switch (request) {
  case 1: // To STATE 1
    analog_control_bits = 0b00; // LP Off (1st 0), Acq Off (2nd 0)
    break;
  case 2: // To STATE 2
    analog_control_bits = 0b10; //LP Off (1st 0), Acq On (2nd 1)
    break;
  case 3:
    analog_control_bits = 0b01; // LP On (1st 1), Acq Off (2nd 0)
    break;
  case 4:
    analog_control_bits = 0b11; // LP On (1st 1), Acq On (2nd 1)
    break;
  default:  //Default state - everything off
    analog_control_bits = 0b00;
    break;    
	}

  // If cycleCounter = 0, then we are not changing states
  // Base the digital filters choices on the request analog bits (request == state in this case)
  if (cycleCounter == 0) {
     for (analog_bit=0 ; analog_bit < 2 ; analog_bit++ ) {
       if (0b1 & (analog_control_bits >> analog_bit)) {
         digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
       } else {
         digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
       }
     }
  // Handle the case where were changing states
  } else {

 // Prior state control bit (used to determine if an analog filter is turning on or off)
  switch (state) {
  case 1: // To STATE 1
    initial_analog_control_bits = 0b00; // LP Off (1st 0), Acq Off (2nd 0)
    break;
  case 2: // To STATE 2
    initial_analog_control_bits = 0b10; //LP Off (1st 0), Acq On (2nd 1)
    break;
  case 3:
    initial_analog_control_bits = 0b01; // LP On (1st 1), Acq Off (2nd 0)
    break;
  case 4:
    initial_analog_control_bits = 0b11; // LP On (1st 1), Acq On (2nd 1)
    break;
  default:  //Default state - everything off
    initial_analog_control_bits = 0b00;
    break;
        }

    // Determine if an analog filter is turning on versus turning off or staying the same
    // 1 indicates that case applies (turn on, turn off, or stay the same)
    digital_turn_on_mask =  (~(initial_analog_control_bits) & analog_control_bits);
    digital_stay_the_same_mask = ~(initial_analog_control_bits ^ analog_control_bits);
  
    // Cycle through all the analog bits
    // Determine if the analog bits are staying the same
    // If so, keep the associated digital filters in the same state
    // If the analog bits are turning on, determine if we've waited long enough, 
    // then change the associated digital filters to the on state.  Otherwise, keep them in the off state.
    // If the analog bits are turning off, determine if we've waited long enough,
    // then change the associated digital filters to the off state.  Otherwise, keep them in the on state.
    for (analog_bit=0 ; analog_bit < 2 ; analog_bit++ ) {
        if (0b1 & (digital_stay_the_same_mask >> analog_bit)) {
          if (0b1 & (analog_control_bits >> analog_bit)) {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
          } else {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
          }
        } else if ( 0b1 & (digital_turn_on_mask >> analog_bit)) {
          if (cycleCounter > cycleDelayTurnOn) {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
        	} else {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
        	}
        } else {
          if (cycleCounter > cycleDelayTurnOff) {
  	  digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
          } else {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
          }
        }
      }
  }  // Finished with the case where states are changingtransition (handles digital filters)

  //Set digital_mask_bits, used by Filter module to determine which filters are under front end control
  //Simple for now - in principle could be made more specific like the above digital control bits and placed
  //inside the state transition code
  if (mask_user_override == 0) {
    digital_mask_bits = 0b0011100111;
  } else {
    digital_mask_bits = 0b0000000000;
  }


  //If coil enabled, need to turn 3rd bit on (add 4)
  if (coilTestEnable == 1) {
    analog_control_bits = analog_control_bits + 4; //Analog filter control bits
  }

  //Send out the calculated bits
  argout[0] = (double) digital_mask_bits;
  argout[1] = (double) digital_control_bits;
  argout[2] = (double) analog_control_bits;
  return;
}

void TACQ(double *argin, int nargin, double *argout, int nargout) {
  
  // Analog filter switching delay -> Cycles to wait before sending command to digital filters
  static long cycleCounter = 0;
  //Last state we finished going to
  static int state = 1;  
  //State we've been requested to go to
  static int request = 1;

  //initialize control bit variables
  int analog_control_bits = 0b0;
  int initial_analog_control_bits = 0b0;
  int digital_control_bits;
  int digital_mask_bits = 0b0;
  int digital_turn_on_mask = 0b0; 
  int digital_stay_the_same_mask = 0b0;
  int analog_to_digital_control[2][2];
  int mask_user_override = 0;

  int analog_bit;

  // Set always on digital control bits
  digital_control_bits = 0b0011100000;

  // Set up digital filter state depending on analog filter state
  analog_to_digital_control[1][0] = 0b0000000010; //Analog Acquire filter Off
  analog_to_digital_control[1][1] = 0b0000000001; //Analog Acquire filter On
  analog_to_digital_control[0][0] = 0b0000000100; //Analog LP filter Off
  analog_to_digital_control[0][1] = 0b0000000000; //Analog LP filter On


  // Read inputs
  int coilTestEnable     = argin[0]; //0 => Digital control for Coil driver, 1 => use Test Analog in
  int epicsStateRequest   = argin[1]; //State request from Epics
  int iscRequest     = argin[2]; // State request from isc
  // Epics input indicating how long to delay digital filter switching in ms when Analog filters are turning ON 
  double msDelayTurnOn = argin[3];
  // Epics input indicating how long to delay digital filter switching in ms when Analog filters are turning OFF 
  double msDelayTurnOff =argin[4];

  // Cycles to delay before switching digital filters
  long cycleDelayTurnOn = msDelayTurnOn * FE_RATE / 1000;  //Used when analog filters turning on
  long cycleDelayTurnOff = msDelayTurnOff * FE_RATE /1000;  //Used when analog filters turning off

  //If we're not already changing states, go ahead and check
  if (cycleCounter == 0) {
    // Epics state 0 => use ISC request
    if (epicsStateRequest == 0) {
      request = iscRequest;
    } else {
      request = epicsStateRequest;
      // Set an a manual override, so user can control digital filters
      // Only affects the mask bits
      if (epicsStateRequest < 0) {
        mask_user_override = 1;
        request = -epicsStateRequest;
      }
    }
  }
  
  //If request is not equal to state, then we are changing states and need to count
  if (request != state) {
    cycleCounter++;
    //We've waited for cycleDelay, now finish the transition to request from state
    if ((cycleCounter > cycleDelayTurnOn) && (cycleCounter > cycleDelayTurnOff)) {
      cycleCounter = 0;
      state = request;
    }
  }


  // Request transitions (handles analog switching)
  switch (request) {
  case 1: // To STATE 1
    analog_control_bits = 0b00; // LP Off (1st 0), Acq Off (2nd 0)
    break;
  case 2: // To STATE 2
    analog_control_bits = 0b10; //LP Off (1st 0), Acq On (2nd 1)
    break;
  case 3:
    analog_control_bits = 0b01; // LP On (1st 1), Acq Off (2nd 0)
    break;
  case 4:
    analog_control_bits = 0b11; // LP On (1st 1), Acq On (2nd 1)
    break;
  default:  //Default state - everything off
    analog_control_bits = 0b00;
    break;    
	}

  // If cycleCounter = 0, then we are not changing states
  // Base the digital filters choices on the request analog bits (request == state in this case)
  if (cycleCounter == 0) {
     for (analog_bit=0 ; analog_bit < 2 ; analog_bit++ ) {
       if (0b1 & (analog_control_bits >> analog_bit)) {
         digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
       } else {
         digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
       }
     }
  // Handle the case where were changing states
  } else {

 // Prior state control bit (used to determine if an analog filter is turning on or off)
  switch (state) {
  case 1: // To STATE 1
    initial_analog_control_bits = 0b00; // LP Off (1st 0), Acq Off (2nd 0)
    break;
  case 2: // To STATE 2
    initial_analog_control_bits = 0b10; //LP Off (1st 0), Acq On (2nd 1)
    break;
  case 3:
    initial_analog_control_bits = 0b01; // LP On (1st 1), Acq Off (2nd 0)
    break;
  case 4:
    initial_analog_control_bits = 0b11; // LP On (1st 1), Acq On (2nd 1)
    break;
  default:  //Default state - everything off
    initial_analog_control_bits = 0b00;
    break;
        }

    // Determine if an analog filter is turning on versus turning off or staying the same
    // 1 indicates that case applies (turn on, turn off, or stay the same)
    digital_turn_on_mask =  (~(initial_analog_control_bits) & analog_control_bits);
    digital_stay_the_same_mask = ~(initial_analog_control_bits ^ analog_control_bits);
  
    // Cycle through all the analog bits
    // Determine if the analog bits are staying the same
    // If so, keep the associated digital filters in the same state
    // If the analog bits are turning on, determine if we've waited long enough, 
    // then change the associated digital filters to the on state.  Otherwise, keep them in the off state.
    // If the analog bits are turning off, determine if we've waited long enough,
    // then change the associated digital filters to the off state.  Otherwise, keep them in the on state.
    for (analog_bit=0 ; analog_bit < 2 ; analog_bit++ ) {
        if (0b1 & (digital_stay_the_same_mask >> analog_bit)) {
          if (0b1 & (analog_control_bits >> analog_bit)) {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
          } else {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
          }
        } else if ( 0b1 & (digital_turn_on_mask >> analog_bit)) {
          if (cycleCounter > cycleDelayTurnOn) {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
        	} else {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
        	}
        } else {
          if (cycleCounter > cycleDelayTurnOff) {
  	  digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
          } else {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
          }
        }
      }
  }  // Finished with the case where states are changingtransition (handles digital filters)

  //Set digital_mask_bits, used by Filter module to determine which filters are under front end control
  //Simple for now - in principle could be made more specific like the above digital control bits and placed
  //inside the state transition code
  if (mask_user_override == 0) {
    digital_mask_bits = 0b0011100111;
  } else {
    digital_mask_bits = 0b0000000000;
  }


  //If coil enabled, need to turn 3rd bit on (add 4)
  if (coilTestEnable == 1) {
    analog_control_bits = analog_control_bits + 4; //Analog filter control bits
  }

  //Send out the calculated bits
  argout[0] = (double) digital_mask_bits;
  argout[1] = (double) digital_control_bits;
  argout[2] = (double) analog_control_bits;
  return;
}




// UIM - handles the 4 OSEM Upper Intermediate Mass stages for QUADs

// Digital Anti Acq, Anti LP1, Anti LP2, Anti LP3 are always ON

//  STATE 1 =>  Analog LP1 OFF, LP2 OFF, LP3 OFF
//		Digital Sim LP1 ON, Sim LP2 ON, Sim LP3 ON
//  STATE 2 => Analog LP1 ON, LP2 OFF, LP3 OFF
//              Digital Sim LP1 OFF, Sim LP2 ON, Sim LP3 ON
//  STATE 3 => Analog LP1 ON, LP2 ON, LP3 OFF
//              Digital Sim LP1 OFF, Sim LP2 OFF, Sim LP3 ON
//  STATE 4 => Analog LP1 ON, LP2 ON, LP3 ON
//              Digital Sim LP1 OFF, Sim LP2 OFF, Sim LP3 OFF

//Takes 4 inputs:
//COIL / TEST ENABLE (0 for Coil or 1 for Test)
//EPICS state request (0 hands control to ISC fast request)
//ISC Fast state request
//Turn On Delay (How many ms to wait before switching digital filters when analog filters are turning on)
//Turn Off Delay (How many ms to wait before switching digital filters when analog filters are turning off)

//Provides 3 outputs:
//argout[0] is Mask bit for Filter module
//argout[1] is Control bit for Filter module
//argout[2] is control bits for BO card
//          1st bit (1) (rightmost) is Low Pass 1 On/Off
//          2nd bit (2) is Low Pass 2 On/Off
//          3rd bit (4) is Low Pass 3 On/Off
//          4th bit (8) is Test Coil Enable


void UIM(double *argin, int nargin, double *argout, int nargout) {
  
  // Analog filter switching delay -> Cycles to wait before sending command to digital filters
  static long cycleCounter = 0;
  //Last state we finished going to
  static int state = 1;  
  //State we've been requested to go to
  static int request = 1;

  //initialize control bit variables
  int analog_control_bits = 0b0;
  int initial_analog_control_bits = 0b0;
  int digital_control_bits;
  int digital_mask_bits = 0b0;
  int digital_turn_on_mask = 0b0; 
  int digital_stay_the_same_mask = 0b0;
  int analog_to_digital_control[3][2];
  int mask_user_override = 0;

  int analog_bit;

  // Set always on digital control bits
  digital_control_bits = 0b0111100000;

  // Set up digital filter state depending on analog filter state
  analog_to_digital_control[2][0] = 0b0000000100; //Analog LP1 filter Off
  analog_to_digital_control[2][1] = 0b0000000000; //Analog LP1 filter On
  analog_to_digital_control[1][0] = 0b0000000010; //Analog LP2 filter Off
  analog_to_digital_control[1][1] = 0b0000000000; //Analog LP2 filter On
  analog_to_digital_control[0][0] = 0b0000000001; //Analog LP3 filter Off
  analog_to_digital_control[0][1] = 0b0000000000; //Analog LP3 filter On

  // Read inputs
  int coilTestEnable     = argin[0]; //0 => Digital control for Coil driver, 1 => use Test Analog in
  int epicsStateRequest   = argin[1]; //State request from Epics
  int iscRequest     = argin[2]; // State request from isc
  // Epics input indicating how long to delay digital filter switching in ms when Analog filters are turning ON 
  double msDelayTurnOn = argin[3];
  // Epics input indicating how long to delay digital filter switching in ms when Analog filters are turning OFF 
  double msDelayTurnOff =argin[4];
  
  // Cycles to delay before switching digital filters
  long cycleDelayTurnOn = msDelayTurnOn * FE_RATE / 1000;  //Used when analog filters turning on
  long cycleDelayTurnOff = msDelayTurnOff * FE_RATE /1000;  //Used when analog filters turning off

  //If we're not already changing states, go ahead and check
  if (cycleCounter == 0) {
    // Epics state 0 => use ISC request
    if (epicsStateRequest == 0) {
      request = iscRequest;
    } else {
      request = epicsStateRequest;
      // Set an a manual override, so user can control digital filters
      // Only affects the mask bits
      if (epicsStateRequest < 0) {
        mask_user_override = 1;
        request = -epicsStateRequest;
      }
    }
  }
  
  //If request is not equal to state, then we are changing states and need to count
  if (request != state) {
    cycleCounter++;
    //We've waited for cycleDelay, now finish the transition to request from state
    if ((cycleCounter > cycleDelayTurnOn) && (cycleCounter > cycleDelayTurnOff)) {
      cycleCounter = 0;
      state = request;
    }
  }

  // Request transitions (handles analog switching)
  switch (request) {
  case 1: // To STATE 1
    analog_control_bits = 0b000; // LP1 Off (0), LP2 Off (0), LP3 Off (0)
    break;
  case 2: // To STATE 2
    analog_control_bits = 0b001; // LP1 On (1), LP2 Off (0), LP3 Off (0)
    break;
  case 3:
    analog_control_bits = 0b011; // LP1 On (1), LP2 On (1), LP3 Off (0)
    break;
  case 4:
    analog_control_bits = 0b111; // LP1 On (1), LP2 On (1), LP3 On (1)
    break;
  default:  //Default state - everything off
    analog_control_bits = 0b000;
    break;    
	}

  // If cycleCounter = 0, then we are not changing states
  // Base the digital filters choices on the request analog bits (request == state in this case)
  if (cycleCounter == 0) {
     for (analog_bit=0 ; analog_bit < 3 ; analog_bit++ ) {
       if (0b1 & (analog_control_bits >> analog_bit)) {
         digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
       } else {
         digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
       }
     }
  // Handle the case where were changing states
  } else {

    // Prior state control bit (used to determine if an analog filter is turning on or off)
    switch (state) {
    case 1: // To STATE 1
      initial_analog_control_bits = 0b000; // LP1 Off (0), LP2 Off (0), LP3 Off (0)
      break;
    case 2: // To STATE 2
      initial_analog_control_bits = 0b001; // LP1 On (1), LP2 Off (0), LP3 Off (0)
      break;
    case 3:
      initial_analog_control_bits = 0b011; // LP1 On (1), LP2 On (1), LP3 Off (0)
      break;
    case 4:
      initial_analog_control_bits = 0b111; // LP1 On (1), LP2 On (1), LP3 On (1)
      break;
    default:  //Default state - everything off
      initial_analog_control_bits = 0b000;
      break;
          }

    // Determine if an analog filter is turning on versus turning off or staying the same
    // 1 indicates that case applies (turn on, turn off, or stay the same)
    digital_turn_on_mask =  (~(initial_analog_control_bits) & analog_control_bits);
    digital_stay_the_same_mask = ~(initial_analog_control_bits ^ analog_control_bits);
  
    // Cycle through all the analog bits
    // Determine if the analog bits are staying the same
    // If so, keep the associated digital filters in the same state
    // If the analog bits are turning on, determine if we've waited long enough, 
    // then change the associated digital filters to the on state.  Otherwise, keep them in the off state.
    // If the analog bits are turning off, determine if we've waited long enough,
    // then change the associated digital filters to the off state.  Otherwise, keep them in the on state.
    for (analog_bit=0 ; analog_bit < 3 ; analog_bit++ ) {
        if (0b1 & (digital_stay_the_same_mask >> analog_bit)) {
          if (0b1 & (analog_control_bits >> analog_bit)) {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
          } else {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
          }
        } else if ( 0b1 & (digital_turn_on_mask >> analog_bit)) {
          if (cycleCounter > cycleDelayTurnOn) {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
        	} else {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
        	}
        } else {
          if (cycleCounter > cycleDelayTurnOff) {
  	  digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
          } else {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
          }
        }
      }
  }  // Finished with the case where states are changing

  //Set digital_mask_bits, used by Filter module to determine which filters are under front end control
  //Simple for now - in principle could be made more specific like the above digital control bits and placed
  //inside the state transition code

  if (mask_user_override == 0) {
    digital_mask_bits = 0b0011100111;
  } else {
    digital_mask_bits = 0b0000000000;
  }


  //If coil enabled, need to turn 4th bit on (add 8)
  if (coilTestEnable == 1) {
    analog_control_bits = analog_control_bits + 8; //Analog filter control bits
  }

  //Send out the calculated bits
  argout[0] = (double) digital_mask_bits;
  argout[1] = (double) digital_control_bits;
  argout[2] = (double) analog_control_bits;
  return;
}

//SINGLE - handles the 4 OSEM top stage

// Digital Anti Acq, Anti Low Pass are always ON

//  STATE 1 =>  Analog Low Pass OFF
//		Sim Low Pass ON
//  STATE 2 =>  Analog Low Pass OFF
//              Sim Low Pass OFF 

//Takes 4 inputs:
//COIL / TEST ENABLE (0 for Coil or 1 for Test)
//EPICS state request (0 hands control to ISC fast request)
//ISC Fast state request0
//Turn On Delay (How many ms to wait before switching digital filters when analog filters are turning on)
//Turn Off Delay (How many ms to wait before switching digital filters when analog filters are turning off)

//Provides 3 outputs:
//argout[0] is Mask bit for Filter module
//argout[1] is Control bit for Filter module
//argout[2] is control bits for BO card
//          1st bit (1) (rightmost) is Low Pass On/Off 
//          2nd bit (2) is Test Coil Enable


void SINGLE(double *argin, int nargin, double *argout, int nargout) {
  
  // Analog filter switching delay -> Cycles to wait before sending command to digital filters
  static long cycleCounter = 0;
  //Last state we finished going to
  static int state = 1;  
  //State we've been requested to go to
  static int request = 1;

  //initialize control bit variables
  int analog_control_bits = 0b0;
  int initial_analog_control_bits = 0b0;
  int digital_control_bits;
  int digital_mask_bits = 0b0;
  int digital_turn_on_mask = 0b0; 
  int digital_stay_the_same_mask = 0b0;
  int analog_to_digital_control[1][2];
  int mask_user_override = 0;

  int analog_bit;

  // Set always on digital control bits
  digital_control_bits = 0b0000100000;

  // Set up digital filter state depending on analog filter state
  analog_to_digital_control[0][0] = 0b0000000001; //Analog LP filter Off
  analog_to_digital_control[0][1] = 0b0000000000; //Analog LP filter On


  // Read inputs
  int coilTestEnable     = argin[0]; //0 => Digital control for Coil driver, 1 => use Test Analog in
  int epicsStateRequest   = argin[1]; //State request from Epics
  int iscRequest     = argin[2]; // State request from isc
  // Epics input indicating how long to delay digital filter switching in ms when Analog filters are turning ON 
  double msDelayTurnOn = argin[3];
  // Epics input indicating how long to delay digital filter switching in ms when Analog filters are turning OFF 
  double msDelayTurnOff =argin[4];

  // Cycles to delay before switching digital filters
  long cycleDelayTurnOn = msDelayTurnOn * FE_RATE / 1000;  //Used when analog filters turning on
  long cycleDelayTurnOff = msDelayTurnOff * FE_RATE /1000;  //Used when analog filters turning off

  //If we're not already changing states, go ahead and check
  if (cycleCounter == 0) {
    // Epics state 0 => use ISC request
    if (epicsStateRequest == 0) {
      request = iscRequest;
    } else {
      request = epicsStateRequest;
      // Set an a manual override, so user can control digital filters
      // Only affects the mask bits
      if (epicsStateRequest < 0) {
        mask_user_override = 1;
        request = -epicsStateRequest;
      }
    }
  }
  
  //If request is not equal to state, then we are changing states and need to count
  if (request != state) {
    cycleCounter++;
    //We've waited for cycleDelay, now finish the transition to request from state
    if ((cycleCounter > cycleDelayTurnOn) && (cycleCounter > cycleDelayTurnOff)) {
      cycleCounter = 0;
      state = request;
    }
  }

  // Request transitions (handles analog switching)
  switch (request) {
  case 1: // To STATE 1
    analog_control_bits = 0b0; // LP Off (0)
    break;
  case 2: // To STATE 2
    analog_control_bits = 0b1; //LP ON (1)
    break;
  default:  //Default state - everything off
    analog_control_bits = 0b0;
    break;    
	}

  // If cycleCounter = 0, then we are not changing states
  // Base the digital filters choices on the request analog bits (request == state in this case)
  if (cycleCounter == 0) {
     for (analog_bit=0 ; analog_bit < 1 ; analog_bit++ ) {
       if (0b1 & (analog_control_bits >> analog_bit)) {
         digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
       } else {
         digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
       }
     }
  // Handle the case where were changing states
  } else {

  // Prior state control bit (used to determine if an analog filter is turning on or off)
  switch (state) {
  case 1: // To STATE 1
    initial_analog_control_bits = 0b0; // LP Off (0)
    break;
  case 2: // To STATE 2
    initial_analog_control_bits = 0b1; //LP ON (1)
    break;
  default:  //Default state - everything off
    initial_analog_control_bits = 0b0;
    break;
        }

    // Determine if an analog filter is turning on versus turning off or staying the same
    // 1 indicates that case applies (turn on, turn off, or stay the same)
    digital_turn_on_mask =  (~(initial_analog_control_bits) & analog_control_bits);
    digital_stay_the_same_mask = ~(initial_analog_control_bits ^ analog_control_bits);
  
    // Cycle through all the analog bits
    // Determine if the analog bits are staying the same
    // If so, keep the associated digital filters in the same state
    // If the analog bits are turning on, determine if we've waited long enough, 
    // then change the associated digital filters to the on state.  Otherwise, keep them in the off state.
    // If the analog bits are turning off, determine if we've waited long enough,
    // then change the associated digital filters to the off state.  Otherwise, keep them in the on state.
    for (analog_bit=0 ; analog_bit < 1 ; analog_bit++ ) {
        if (0b1 & (digital_stay_the_same_mask >> analog_bit)) {
          if (0b1 & (analog_control_bits >> analog_bit)) {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
          } else {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
          }
        } else if ( 0b1 & (digital_turn_on_mask >> analog_bit)) {
          if (cycleCounter > cycleDelayTurnOn) {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
        	} else {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
        	}
        } else {
          if (cycleCounter > cycleDelayTurnOff) {
  	  digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
          } else {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
          }
        }
      }
  }  // Finished with the case where states are changing

  //Set digital_mask_bits, used by Filter module to determine which filters are under front end control
  //Simple for now - in principle could be made more specific like the above digital control bits and placed
  //inside the state transition code
  if (mask_user_override == 0) {
    digital_mask_bits = 0b0000100001;
  } else {
    digital_mask_bits = 0b0000000000;
  }


  //If coil enabled, need to turn 2nd bit on (add 2)
  if (coilTestEnable == 1) {
    analog_control_bits = analog_control_bits + 2; //Analog filter control bits
  }

  //Send out the calculated bits
  argout[0] = (double) digital_mask_bits;
  argout[1] = (double) digital_control_bits;
  argout[2] = (double) analog_control_bits;
  return;
}



// KAGRA_CD - KAGRA Coil Driver controller
// updated 2018/4/27 Arai

// Digital Anti Acq, Anti LP1, Anti LP2, Anti LP3 are always ON

//  STATE 1 =>  Analog LP1 OFF, LP2 OFF, LP3 OFF
//		Digital Sim LP1 ON, Sim LP2 ON, Sim LP3 ON
//  STATE 2 => Analog LP1 ON, LP2 OFF, LP3 OFF
//              Digital Sim LP1 OFF, Sim LP2 ON, Sim LP3 ON
//  STATE 3 => Analog LP1 ON, LP2 ON, LP3 OFF
//              Digital Sim LP1 OFF, Sim LP2 OFF, Sim LP3 ON
//  STATE 4 => Analog LP1 ON, LP2 ON, LP3 ON
//              Digital Sim LP1 OFF, Sim LP2 OFF, Sim LP3 OFF
//  STATE 5 => Analog LP1 OFF, LP2 ON, LP3 OFF
//              Digital Sim LP1 ON, Sim LP2 OFF, Sim LP3 ON
//  STATE 6 => Analog LP1 OFF, LP2 OFF, LP3 ON
//              Digital Sim LP1 ON, Sim LP2 ON, Sim LP3 OFF

//Takes 4 inputs:
//COIL / TEST ENABLE (0 for Coil or 1 for Test)
//EPICS state request (0 hands control to ISC fast request)
//ISC Fast state request
//Turn On Delay (How many ms to wait before switching digital filters when analog filters are turning on)
//Turn Off Delay (How many ms to wait before switching digital filters when analog filters are turning off)

//Provides 3 outputs:
//argout[0] is Mask bit for Filter module
//argout[1] is Control bit for Filter module
//argout[2] is control bits for BO card
//          1st bit (1) (rightmost) is Low Pass 1 On/Off
//          2nd bit (2) is Low Pass 2 On/Off
//          3rd bit (4) is Low Pass 3 On/Off
//          4th bit (8) is Test Coil Enable


void KAGRA_CD(double *argin, int nargin, double *argout, int nargout) {
  
  // Analog filter switching delay -> Cycles to wait before sending command to digital filters
  static long cycleCounter = 0;
  //Last state we finished going to
  static int state = 1;  
  //State we've been requested to go to
  static int request = 1;

  //initialize control bit variables
  int analog_control_bits = 0b0;
  int initial_analog_control_bits = 0b0;
  int digital_control_bits;
  int digital_mask_bits = 0b0;
  int digital_turn_on_mask = 0b0; 
  int digital_stay_the_same_mask = 0b0;
  int analog_to_digital_control[3][2];
  int mask_user_override = 0;

  int analog_bit;

  // Set always on digital control bits
  digital_control_bits = 0b0111100000;

  // Set up digital filter state depending on analog filter state
  analog_to_digital_control[2][0] = 0b0000000100; //Analog LP1 filter Off
  analog_to_digital_control[2][1] = 0b0000000000; //Analog LP1 filter On
  analog_to_digital_control[1][0] = 0b0000000010; //Analog LP2 filter Off
  analog_to_digital_control[1][1] = 0b0000000000; //Analog LP2 filter On
  analog_to_digital_control[0][0] = 0b0000000001; //Analog LP3 filter Off
  analog_to_digital_control[0][1] = 0b0000000000; //Analog LP3 filter On

  // Read inputs
  int coilTestEnable     = argin[0]; //0 => Digital control for Coil driver, 1 => use Test Analog in
  int epicsStateRequest   = argin[1]; //State request from Epics
  int iscRequest     = argin[2]; // State request from isc
  // Epics input indicating how long to delay digital filter switching in ms when Analog filters are turning ON 
  double msDelayTurnOn = argin[3];
  // Epics input indicating how long to delay digital filter switching in ms when Analog filters are turning OFF 
  double msDelayTurnOff =argin[4];
  
  // Cycles to delay before switching digital filters
  long cycleDelayTurnOn = msDelayTurnOn * FE_RATE / 1000;  //Used when analog filters turning on
  long cycleDelayTurnOff = msDelayTurnOff * FE_RATE /1000;  //Used when analog filters turning off

  //If we're not already changing states, go ahead and check
  if (cycleCounter == 0) {
    // Epics state 0 => use ISC request
    if (epicsStateRequest == 0) {
      request = iscRequest;
    } else {
      request = epicsStateRequest;
      // Set an a manual override, so user can control digital filters
      // Only affects the mask bits
      if (epicsStateRequest < 0) {
        mask_user_override = 1;
        request = -epicsStateRequest;
      }
    }
  }
  
  //If request is not equal to state, then we are changing states and need to count
  if (request != state) {
    cycleCounter++;
    //We've waited for cycleDelay, now finish the transition to request from state
    if ((cycleCounter > cycleDelayTurnOn) && (cycleCounter > cycleDelayTurnOff)) {
      cycleCounter = 0;
      state = request;
    }
  }

  // Request transitions (handles analog switching)
  switch (request) {
  case 1: // To STATE 1
    analog_control_bits = 0b000; // LP1 Off (0), LP2 Off (0), LP3 Off (0)
    break;
  case 2: // To STATE 2
    analog_control_bits = 0b001; // LP1 On (1), LP2 Off (0), LP3 Off (0)
    break;
  case 3:
    analog_control_bits = 0b011; // LP1 On (1), LP2 On (1), LP3 Off (0)
    break;
  case 4:
    analog_control_bits = 0b111; // LP1 On (1), LP2 On (1), LP3 On (1)
    break;
  case 5:
    analog_control_bits = 0b010; // LP1 Off (0), LP2 On (1), LP3 Off (0)
    break;
  case 6:
    analog_control_bits = 0b100; // LP1 Off (0), LP2 Off (0), LP3 On (1)
    break;
  default:  //Default state - everything off
    analog_control_bits = 0b000;
    break;    
	}

  // If cycleCounter = 0, then we are not changing states
  // Base the digital filters choices on the request analog bits (request == state in this case)
  if (cycleCounter == 0) {
     for (analog_bit=0 ; analog_bit < 3 ; analog_bit++ ) {
       if (0b1 & (analog_control_bits >> analog_bit)) {
         digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
       } else {
         digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
       }
     }
  // Handle the case where were changing states
  } else {

    // Prior state control bit (used to determine if an analog filter is turning on or off)
    switch (state) {
    case 1: // To STATE 1
      initial_analog_control_bits = 0b000; // LP1 Off (0), LP2 Off (0), LP3 Off (0)
      break;
    case 2: // To STATE 2
      initial_analog_control_bits = 0b001; // LP1 On (1), LP2 Off (0), LP3 Off (0)
      break;
    case 3:
      initial_analog_control_bits = 0b011; // LP1 On (1), LP2 On (1), LP3 Off (0)
      break;
    case 4:
      initial_analog_control_bits = 0b111; // LP1 On (1), LP2 On (1), LP3 On (1)
      break;
    case 5:
      initial_analog_control_bits = 0b010; // LP1 Off (0), LP2 On (1), LP3 Off (0)
      break;
    case 6:
      initial_analog_control_bits = 0b100; // LP1 Off (0), LP2 Off (0), LP3 On (1)
      break;
    default:  //Default state - everything off
      initial_analog_control_bits = 0b000;
      break;
          }

    // Determine if an analog filter is turning on versus turning off or staying the same
    // 1 indicates that case applies (turn on, turn off, or stay the same)
    digital_turn_on_mask =  (~(initial_analog_control_bits) & analog_control_bits);
    digital_stay_the_same_mask = ~(initial_analog_control_bits ^ analog_control_bits);
  
    // Cycle through all the analog bits
    // Determine if the analog bits are staying the same
    // If so, keep the associated digital filters in the same state
    // If the analog bits are turning on, determine if we've waited long enough, 
    // then change the associated digital filters to the on state.  Otherwise, keep them in the off state.
    // If the analog bits are turning off, determine if we've waited long enough,
    // then change the associated digital filters to the off state.  Otherwise, keep them in the on state.
    for (analog_bit=0 ; analog_bit < 3 ; analog_bit++ ) {
        if (0b1 & (digital_stay_the_same_mask >> analog_bit)) {
          if (0b1 & (analog_control_bits >> analog_bit)) {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
          } else {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
          }
        } else if ( 0b1 & (digital_turn_on_mask >> analog_bit)) {
          if (cycleCounter > cycleDelayTurnOn) {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
        	} else {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
        	}
        } else {
          if (cycleCounter > cycleDelayTurnOff) {
  	  digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][0];
          } else {
            digital_control_bits = digital_control_bits | analog_to_digital_control[analog_bit][1];
          }
        }
      }
  }  // Finished with the case where states are changing

  //Set digital_mask_bits, used by Filter module to determine which filters are under front end control
  //Simple for now - in principle could be made more specific like the above digital control bits and placed
  //inside the state transition code

  if (mask_user_override == 0) {
    digital_mask_bits = 0b0011100111;
  } else {
    digital_mask_bits = 0b0000000000;
  }


  //If coil enabled, need to turn 4th bit on (add 8)
  if (coilTestEnable == 1) {
    analog_control_bits = analog_control_bits + 8; //Analog filter control bits
  }

  //Send out the calculated bits
  argout[0] = (double) digital_mask_bits;
  argout[1] = (double) digital_control_bits;
  argout[2] = (double) analog_control_bits;
  return;
}
