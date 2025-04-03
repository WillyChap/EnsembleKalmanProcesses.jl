#!/usr/bin/env bash

export CESM_ROOT=/glade/work/wchapman/cesm_sandboxes/cesm_moving_mountains_04032025/

module load conda
conda activate npl-2023b


## python build_EKI_CAM_cases.py --cesmroot /glade/work/wchapman/cesm_sandboxes/cesm_moving_mountains_04032025/ --basecasename GW_EKI_test_01
