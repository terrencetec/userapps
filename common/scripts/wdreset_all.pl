#!/usr/bin/perl -I /kagra/cdscfg

use strict; use warnings;
use stdenv;
INIT_ENV($ENV{IFO});
use lib $ENV{USERAPPS_DIR} . '/guardian';
use CaTools;

# This script attempts to reset the watchdog, then the DACKILL.
# If successful, returns with 0 status.
# If fails, tries to print a reason, exits with status 1.
# Accepts 1 argument: the subsystem name

# Usage: ./wdreset_all H1:SUS-ETMX

my $SubSys = uc(shift);

caPut("${SubSys}_WD_RESET", 1);
sleep(1);
caPut("${SubSys}_DACKILL_RESET", 1);
