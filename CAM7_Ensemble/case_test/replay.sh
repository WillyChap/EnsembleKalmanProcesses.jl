#!/bin/bash

set -e

# Created 2025-04-04 13:03:41

CASEDIR="/glade/work/wchapman/MovingMountains_Calibrate/CAM7_Ensemble/case_test"

/glade/work/wchapman/cesm_sandboxes/cesm_moving_mountains_04032025/cime/scripts/create_newcase --case ./case_test --mach derecho --res ne30pg3_ne30pg3_mt232 --compset FHISTC_MTso

cd "${CASEDIR}"

