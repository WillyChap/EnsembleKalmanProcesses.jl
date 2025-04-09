#!/usr/bin/env python3
      
import os, sys
import subprocess
from netCDF4 import Dataset
from itertools import islice
import argparse

# This script must be run in an environment with netCDF4 python libraries 
# active and the ability to build cesm cases.
# On Cheyenne, the best way to do this is from an interactive session.
# > qsub -X -I -l select=1:ncpus=36:mpiprocs=36 -l walltime=02:30:00 -q regular -A P93300642
# > conda activate my_env+++
# > ./build_ppe_CAM_cases.py

# Edit below to set up your cases
# cesmroot = '/glade/u/home/trude/src/cam6_3_026_ppe/'
# cesmroot = '/glade/work/wchapman/supermodel_derecho_conda/'
# basecasename = "GW_EKI_test_01"
# baseroot = os.path.join("/glade/work/wchapman/cesm/EKI_GWP_RUNS/","gwp_cases",basecasename)


res = "ne30pg3_ne30pg3_mt232"
compset = "FHISTC_MTso"
#compset = "FHIST"
#res = "f09_f09_mg17"

paramfile = "/glade/work/wchapman/MovingMountains_Calibrate/examples/ClimateMachine/clima_parameters_000.nc"
# paramfile = "./CESM_parameter_229_231.nc"

# ++TE: do not change ensemble_startval
ensemble_startval = "001" # The startval strings should be the same length, or else. 
basecase_startval = "000"
project = "P03010039"
wall_time = "03:00:00"
ntasks = 1920

specify_user_num_sims = True # If True, use "user_num_sims" number of sims. This will
                             # use the first X values of each parameter, and will 
                             # probably crash if you specify more simulations than
                             # parameter values in your paramfile. 
                             # If False, automatically create the same number of cases
                             # as param values in the paramfile. This is the safest 
                             # option.
user_num_sims = 4

specify_sstice_file = False   # If true, the base case will be updated with the following
                             # SSTICE file settings, if false, these will not be used.
sstice_filename = "$DIN_LOC_ROOT/atm/cam/sst/sst_HadOIBl_bc_1x1_2000climo_c180511.nc"
sstice_yr_align = 1
sstice_yr_start = 0
sstice_yr_end   = 0

# Currently only number of years set (no months or days)
# Will be the same in every case

stop_yrs = 3
rest_yrs = 1
run_type = "hybrid"
start_date = "2014-01-01"

# REFCASE settings below are optional
# Will be the same in every case

#ref_case_get = True
#ref_case_name = "f.e20.FHIST.f09_f09.cesm2_1.001_v2"
#ref_case_path = "cesm2_init"
#ref_case_date = "2000-01-01"

## CAM_CONFIG_OPTS
# cam_conopts = "-cosp"

## CAM SourceMods
camSourceModsPath = "/glade/work/pel/cesm_tags/PPE/SourceMods/src.cam/*.F90"
#clmSourceModsPath = "/glade/campaign/cesm/cesmdata/cseg/runs/cesm2_0/f.cam6_3_119.FLTHIST_ne30.r328_gamma0.33_soae.001/SourceMods/src.clm/*"

## User_nl_cam text that will be cloned in every ensemble case
## Text in user_nl_cam will appear exactly as in this string specifier
user_nl_cam_string = """
mfilt    =       0,       5  
nhtfrq              =       0,     -24  
ndens               =       2,       2 

empty_htapes = .true.

fincl1 = 'U','V','T','Q'
                                       
"""
## No /EOF needed for python

## User_nl_clm text that will be cloned in every ensemble case
## Text in user_nl_cam will appear exactly as in this string specifier
user_nl_clm_string = """
use_init_interp = .true.
check_finidat_year_consistency = .false.

"""
## No /EOF needed for python

## Should not be a need to edit below this line ##


def per_run_case_updates(case, ensemble_str, nint, paramdict, ensemble_idx):
    print(">>>>> BUILDING CLONE CASE...")
    caseroot = case.get_value("CASEROOT")
    basecasename = os.path.basename(caseroot)[:-nint]

    unlock_file("env_case.xml",caseroot=caseroot)
    casename = basecasename+ensemble_str
    case.set_value("CASE",casename)
    rundir = case.get_value("RUNDIR")
    rundir = rundir[:-nint]+ensemble_str
    case.set_value("RUNDIR",rundir)
    case.flush()
    lock_file("env_case.xml",caseroot=caseroot)
    print("...Casename is {}".format(casename))
    print("...Caseroot is {}".format(caseroot))
    print("...Rundir is {}".format(rundir))

    # Add user_nl updates for each run                                                        

    paramLines = []
#    ens_idx = int(ensemble_str)-int(ensemble_startval)
    ens_idx = int(ensemble_idx)-int(ensemble_startval)
    print('ensemble_index')
    print(ens_idx)
    for var in paramdict.keys():
        paramLines.append("{} = {}\n".format(var,paramdict[var][ens_idx]))

    usernlfile = os.path.join(caseroot,"user_nl_cam")
    print("...Writing to user_nl file: "+usernlfile)
    file1 = open(usernlfile, "a")
    # file1.writelines(paramLines) #this is where the new parameters will be added to the clone. 
    file1.close()

    print(">> Clone {} case_setup".format(ensemble_str))
    case.case_setup()
    print(">> Clone {} create_namelists".format(ensemble_str))
    case.create_namelists()
    print(">> Clone {} submit".format(ensemble_str))
    #case.submit() #to submit the case. 


def build_base_case(baseroot, basecasename, res, compset, overwrite, cesmroot):
    print(">>>>> BUILDING BASE CASE...")
    caseroot = os.path.join(baseroot,basecasename+'.'+basecase_startval)
    if overwrite and os.path.isdir(caseroot):
        shutil.rmtree(caseroot)
    with Case(caseroot, read_only=False) as case:
        if not os.path.isdir(caseroot):
            print('pre case', os.path.basename(caseroot))
            case.create(os.path.basename(caseroot), cesmroot, compset, res,
                        machine_name="derecho",
                        run_unsupported=True, answer="r", walltime=wall_time, 
                        project=project, driver='nuopc')
            print('post case')
            # make sure that changing the casename will not affect these variables                                           
            case.set_value("EXEROOT",case.get_value("EXEROOT", resolved=True))
            case.set_value("RUNDIR",case.get_value("RUNDIR",resolved=True)+".00")

        #case.set_value("RUN_TYPE",run_type)
        #case.set_value("GET_REFCASE",ref_case_get)
        #case.set_value("RUN_REFCASE",ref_case_name)
        #case.set_value("RUN_REFDIR",ref_case_path)
        #case.set_value("RUN_REFDATE",ref_case_date)
        case.set_value("STOP_OPTION","nyears")
        case.set_value("STOP_N",stop_yrs)
        case.set_value("REST_OPTION","nyears")
        case.set_value("REST_N",rest_yrs)
        case.set_value("RUN_STARTDATE",start_date)

        #case.set_value("NTASKS",ntasks)
        #case.set_value("NTASKS_GLC",1)
        #case.set_value("NTASKS_WAV",1)
        #case.set_value("NTASKS_ESP",1)

        # case.set_value("CAM_CONFIG_OPTS", 
        #                case.get_value("CAM_CONFIG_OPTS",resolved=True)+' '+cam_conopts)
        if specify_sstice_file:
            case.set_value("SSTICE_DATA_FILENAME",sstice_filename)
            case.set_value("SSTICE_YEAR_ALIGN",sstice_yr_align)
            case.set_value("SSTICE_YEAR_START",sstice_yr_start)
            case.set_value("SSTICE_YEAR_END",sstice_yr_end)

        case.set_value("SSTICE_YEAR_ALIGN", 2014)

#            case.set_value("QUEUE","economy")

        rundir = case.get_value("RUNDIR")
        caseroot = case.get_value("CASEROOT")

        print('caseroot:', caseroot)
        print('caseroot:', caseroot)
        print('caseroot:', caseroot)
        print('caseroot:', caseroot)
        print('caseroot:', caseroot)
        
        print(">> base case_setup...")
        case.case_setup()

        print(">> base SourceMods copy...")
        camSrcPath = os.path.join(caseroot,"SourceMods","src.cam")
        #subprocess.check_call("cp "+camSourceModsPath+" "+camSrcPath, shell=True)
        clmSrcPath = os.path.join(caseroot,"SourceMods","src.clm")
        #subprocess.check_call("cp "+clmSourceModsPath+" "+clmSrcPath, shell=True)


        
        
        print(">> base case write user_nl_cam...")
        usernlfile = os.path.join(caseroot,"user_nl_cam")
        funl = open(usernlfile, "a")
        funl.write(user_nl_cam_string)
        funl.close()

        print(">> base case write user_nl_clm...")
        usernlfile = os.path.join(caseroot,"user_nl_clm")
        funl = open(usernlfile, "a")
        funl.write(user_nl_clm_string)
        funl.close()
        
        print(">> base case_build...")
        build.case_build(caseroot, case=case)
        subprocess.check_call("./preview_namelists", shell=True)
        subprocess.check_call("./case.build", shell=True)

        return caseroot

def clone_base_case(caseroot, ensemble, overwrite, paramdict, ensemble_num):
    print(">>>>> CLONING BASE CASE...")
    print(ensemble)
    startval = ensemble_startval
    nint = len(ensemble_startval)
    cloneroot = caseroot
    for i in range(int(startval), int(startval)+ensemble):
        ensemble_idx = '{{0:0{0:d}d}}'.format(nint).format(i)
        member_string = ensemble_num[i-1]
        print("member_string="+member_string)
        if ensemble > 1:
            caseroot = caseroot[:-nint] + member_string
        if overwrite and os.path.isdir(caseroot):
            shutil.rmtree(caseroot)
        if not os.path.isdir(caseroot):
            with Case(cloneroot, read_only=False) as clone:
                clone.create_clone(caseroot, keepexe=True)
        with Case(caseroot, read_only=False) as case:
            per_run_case_updates(case, member_string, nint, paramdict, ensemble_idx)


def parse_arguments():
    parser = argparse.ArgumentParser(description="CESM case creation and execution script")
    parser.add_argument("--cesmroot", type=str, required=True, help="Path to CESM root directory")
    parser.add_argument("--basecasename", type=str, required=True, help="Base case name")
    return parser.parse_args()


def take(n, iterable):
    "Return first n items of the iterable as a list"
    return list(islice(iterable, n))


def _main_func(cesmroot, basecasename):

    print ("Starting SCAM PPE case creation, building, and submission script")
    print ("Base case name is {}".format(basecasename))
    print ("Parameter file is "+paramfile)

    baseroot = os.path.join("/glade/work/wchapman/cesm/EKI_GWP_RUNS/","gwp_cases", basecasename)

    overwrite = True

    # read in NetCDF parameter file
    inptrs = Dataset(paramfile,'r')
    print ("Variables in paramfile:")
    print (inptrs.variables.keys())
    print ("Dimensions in paramfile:")
    print (inptrs.dimensions.keys())
    num_sims = inptrs.dimensions['nmb_sim'].size
    num_vars = len(inptrs.variables.keys())-1
    ensemble_num = inptrs['Sample_nmb']
    print('ensemble_num')
    print('look:',ensemble_num)
    print(ensemble_num[0])
    print(ensemble_num[1])
    print(ensemble_num[2])
    print(ensemble_num[3])
    
    if specify_user_num_sims:
        num_sims = user_num_sims

    print ("Number of sims = {}".format(num_sims))
    print ("Number of params = {}".format(num_vars))


    # Save a pointer to the netcdf variables
    paramdict = inptrs.variables
    del paramdict['Sample_nmb']

    # Create and build the base case that all PPE cases are cloned from
    caseroot = build_base_case(baseroot, basecasename, res,
                                   compset, overwrite, cesmroot)

    # Pass in a dictionary with all of the parameters and their values
    # for each PPE simulation 
    # This code clones the base case, using the same build as the base case,
    # Adds the namelist parameters from the paramfile to the user_nl_cam 
    # file of each new case, does a case.set up, builds namelists, and 
    # submits the runs.

    clone_base_case(caseroot, num_sims, overwrite, paramdict, ensemble_num)

    inptrs.close()

if __name__ == "__main__":
    args = parse_arguments()
    print("Example usage:")
    print("python script.py --cesmroot /path/to/cesm --basecasename MyCaseName")



    if args.cesmroot is None:
        raise SystemExit("ERROR: CESM_ROOT must be defined in environment")


    _LIBDIR = os.path.join(args.cesmroot,"cime","scripts","Tools")
    sys.path.append(_LIBDIR)
    _LIBDIR = os.path.join(args.cesmroot,"cime","scripts","lib")
    sys.path.append(_LIBDIR)
    
    
    _LIBDIR = os.path.join(args.cesmroot,"cime","CIME","Tools")
    sys.path.append(_LIBDIR)
    _LIBDIR = os.path.join(args.cesmroot,"cime")
    sys.path.append(_LIBDIR)
    
    print(_LIBDIR)
    print(_LIBDIR)
    print(_LIBDIR)
    print(_LIBDIR)
    import datetime, glob, shutil
    import CIME.build as build
    from standard_script_setup import *
    from CIME.case             import Case
    from CIME.utils            import safe_copy
    from argparse              import RawTextHelpFormatter
    from CIME.locked_files          import lock_file, unlock_file

    _main_func(args.cesmroot, args.basecasename)

