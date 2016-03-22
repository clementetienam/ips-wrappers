#! /usr/bin/env python

"""
generic_init.py  Batchelor (2-15-2016)

The Swiss army knife of Plasma State initializers.

This version combines several previous initializer routines and extends them.  There are
X modes of initialization to be specified by the config file variable INIT_MODE

INIT_MODE = minimal
This is exactly the same as the previous generic_ps_init.py. It produces a CURRENT_STATE 
that is empty except for some metadata:
time variables - ps%t0, ps%t1, ps%tinit, and ps%tfinal 
simulation identifiers - ps%tokamak_id, ps%shot_number, ps%run_id.  
ps%Global_label is set to run_id_tokamak_id_shot_number.
This data is set for all initialization modes, but for 'minimal' this is all that is done.

INIT_MODE = existing_ps_file
This copies an existing input plasma state file

INIT_MODE = mdescr
This initializes all machine description data from a plasma state machine description 
file <tokamak>.mdescr

INIT_MODE = mixed (yet to be implemented)

"""

# version 4.0 5/21/2010 (Batchelor)
#--------------------------------------------------------------------------
#
# This version supports both checkpoint and restart using framework functions
# A checkpoint() function is provided that is called by the framework 
# services.checkpoint_components() fnction.  The restart priocess now uses framwork 
# function get_restart_files() in 'step'.  There is no 'restart' function for the
# INIT component.

# version 2.0 2/4/2010 (Batchelor)
#--------------------------------------------------------------------------
#
# The 'init' component produces a complete set of (almost) empty plasma state files
# and puts them in the plasma state work directory to be further populated by the
# 'init' functions of the other components.  This version only generates files that
# are called out as global config parameters in the config file.  As of now
# the files that it looks for include [CURRENT_STATE, PRIOR_STATE, NEXT_STATE,
# CURRENT_EQDSK, CURRENT_CQL, CURRENT_DQL, CURRENT_EQDSK].  We can always add more.
#
# This produces a CURRENT_STATE that is empty except for:
# time variables - ps%t0, ps%t1, ps%tinit, and ps%tfinal 
# simulation identifiers - ps%tokamak_id, ps%shot_number, ps%run_id.  
# ps%Global_label is set to run_id_tokamak_id_shot_number.
#
# This component drives the fortran executable generic_ps_init.f90 which uses
# Plasma State calls to generate CURRENT_STATE
#
# This version also supports RESTART as specified by the SIMULATION_MODE variable in
# the config file.  For a restart run the plasma state files are retrieved 
# by the framework from the path indicated by the INPUT_DIR config parameter in the 
# [generic_ps_init] section.  The new values of ps%t0 and ps%tfinal are written into
# CURRENT_STATE, and CURRENT_STATE is copied to PRIOR_STATE and NEXT_STATE if these are
# in the PLASMA_STATE_FILES list.  The state files are copied to the plasma state work
# directory by services.update_plasma_state().
#
# Nota Bene: For restart the plasma state files should be listed in the config file as  
# input files to the generic_ps_init component.
#
# N.B. The other plasma state files that in previous versions were produced by the
#      fortran code are now produced here. These files include:
#      prior_state file and next_state file as well as the dummy files: cur_cql_file
#      cur_eqdsk_file, cur_dql_file, and cur_jsdsk_file.
#
# N.B. Both ps%t0 and ps%t1 are set to the value time_stamp.  tinit and tfinal
#      are generated here from the TIME_LOOP variable in the
#      simulation config file.  Note that the initial t0 can be different from 
#      tinit, as might be needed in a restart.
#
# ------------------------------------------------------------------------------

import sys
import os
import subprocess
import getopt
import shutil
import string
from  component import Component
from netCDF4 import *

class generic_ps_init (Component):
    def __init__(self, services, config):
        Component.__init__(self, services, config)
        print 'Created %s' % (self.__class__)

# ------------------------------------------------------------------------------
#
# init function
#
# Does nothing.
#
# ------------------------------------------------------------------------------

    def init(self, timestamp=0.0):
        print (' ')
        print ('generic_ps_init.init() called')
        return

# ------------------------------------------------------------------------------
#
# step function
#
# Calls fortran executable init_empty_plasma_state and updates plasma state
#
# ------------------------------------------------------------------------------

    def step(self, timeStamp):
        print (' ')
        print ('generic_ps_init.step() called')

        services = self.services

# Get timeloop for simulation
        timeloop = services.get_time_loop()
        tlist_str = ['%.3f'%t for t in timeloop]
        t = tlist_str[0]
        tinit  = tlist_str[0]
        tfinal  = tlist_str[-1]

# Check if this is a restart simulation
        mode = self.try_get_config_param(services, 'SIMULATION_MODE')

        if mode == 'RESTART':
            print 'generic_ps_init: RESTART'
        if mode not in ['RESTART', 'NORMAL']:
            logMsg = 'generic_ps_init: unrecoginzed SIMULATION_MODE: ' + mode
            self.services.error(logMsg)
            raise ValueError(logMsg)
 
# ------------------------------------------------------------------------------
#
# RESTART simulation mode
#
# ------------------------------------------------------------------------------
            
        if mode == 'RESTART':
            # Get restart files listed in config file. Here just the plasma state files.
            restart_root = self.get_config_parameter('RESTART_ROOT')
            restart_time = self.get_config_parameter('RESTART_TIME')
            try:
                 services.get_restart_files(restart_root, restart_time, self.RESTART_FILES)
            except:
                logMsg = 'Error in call to get_restart_files()'
                self.services.exception(logMsg)
                raise
            
            cur_state_file = self.services.get_config_param('CURRENT_STATE')
    
            # Update ps%t0, ps%t1 and ps%tfinal. 
            # Note ps%tinit stays the same in the plasma state file, 
            # tinit from the config file timeloop is the restart time 
            ps = Dataset(cur_state_file, 'r+', format = 'NETCDF3_CLASSIC')
            ps.variables['t0'].assignValue(float(tinit))
            ps.variables['t1'].assignValue(float(tinit))
            ps.variables['tfinal'].assignValue(float(tfinal))
            ps.close()
        
# ------------------------------------------------------------------------------
#
# NORMAL simulation mode
#
# ------------------------------------------------------------------------------
        
        else:
            print 'generic_ps_init: simulation mode NORMAL'
            ps_file_list = self.try_get_config_param(services, 'PLASMA_STATE_FILES').split(' ')
 
            try:       
                services.stage_input_files(self.INPUT_FILES)
            except Exception:
                message = 'generic_ps_init: Error in staging input files'
                print message
                services.exception(message)
                raise

            cur_state_file = self.try_get_config_param(services, 'CURRENT_STATE')

            init_mode = self.try_get_component_param(services,'INIT_MODE')
            print 'generic_ps_init: INIT_MODE = ', INIT_MODE

            # init from existing plasma state file
            if init_mode == 'existing_ps_file' or 'EXISTING_PS_FILE' :    
                INPUT_STATE_FILE = self.get_config_parameter('INPUT_STATE_FILE')
                INPUT_EQDSK_FILE = self.get_config_parameter('INPUT_EQDSK_FILE', optional)
     
                # Copy INPUT_STATE_FILE to current state file
                try:
                    subprocess.call(['cp', INPUT_STATE_FILE, cur_state_file ])
                except Exception:
                    message = 'generic_ps_init: Error in copying INPUT_STATE_FILE \
                        to current state file'
                    print message
                    services.exception(message)
                    raise

            # init from machine description file
            if init_mode == 'mdescr' or 'MDESCR' :
                print 'MDESCR not implemented yet'
                raise
                mdescr_file = self.get_config_parameter('MDESCR_FILE')
                


            init_bin = os.path.join(self.BIN_PATH, 'generic_ps_init')
    
            print 'Executing ', [init_bin, cur_state_file]
            retcode = subprocess.call([init_bin, cur_state_file, 
                tokamak, shot_number, run_id, tinit, tfinal, t])
            if (retcode != 0):
               print 'Error executing ', init_bin
               raise

            # For all init init modes insert run identifiers and time data 
            # (do it here in python instead of in minimal_state_init.f90 as before)
            # For minimal this is the only thing done
            tokamak = self.get_config_parameter('TOKAMAK_ID', optional)
            shot_number = self.get_config_parameter('SHOT_NUMBER', optional)
            run_id = self.get_config_parameter('RUN_ID', optional)

            timeloop = services.get_time_loop()
            t0 = timeloop[0]
            t1 = t0
            tfinal = timeloop[-1]

            # Put into current plasma state
            plasma_state = Dataset(cur_state_file, 'r', format = 'NETCDF3_CLASSIC')
            plasma_state.variables['tokamak_id'] = tokamak
            plasma_state.variables['shot_number'] = shot_number
            plasma_state.variables['run_id'] = run_id
            plasma_state.variables['t0'] = t0
            plasma_state.variables['t1'] = t1
            plasma_state.variables['tinit'] = t0
            plasma_state.variables['tfinal'] = tfinal
            plasma_state.close()
               
        # Generate other state files as dummies so framework will have a complete set
            for file in ps_file_list:
                print 'touching plasma state file = ', file
                try:
                    subprocess.call(['touch', file])
                except Exception:
                    print 'No file ', file

        # For benefit of framework file handling generate dummy dakota.out file
        subprocess.call(['touch', 'dakota.out'])

        # Copy current plasma state to prior state and next state
        try:
            prior_state_file = services.get_config_param('PRIOR_STATE')
            shutil.copyfile(cur_state_file, prior_state_file)
        except Exception, e:
            print 'No PRIOR_STATE file ', e

        try:
            next_state_file = services.get_config_param('NEXT_STATE')
            shutil.copyfile(cur_state_file, next_state_file)
        except Exception, e:
            print 'No NEXT_STATE file ', e


# Update plasma state
        try:
            services.update_plasma_state()
        except Exception, e:
            print 'Error in call to updatePlasmaState()', e
            raise

# "Archive" output files in history directory
        services.stage_output_files(timeStamp, self.OUTPUT_FILES)

# ------------------------------------------------------------------------------
#
# checkpoint function
#
# Saves plasma state files to restart directory
# ------------------------------------------------------------------------------

    def checkpoint(self, timestamp=0.0):
        print 'generic_ps_init.checkpoint() called'
        
        services = self.services
        services.stage_plasma_state()
        services.save_restart_files(timestamp, self.RESTART_FILES)
        

# ------------------------------------------------------------------------------
#
# finalize function
#
# Does nothing
# ------------------------------------------------------------------------------



    def finalize(self, timestamp=0.0):
        print 'generic_ps_init.finalize() called'

# ------------------------------------------------------------------------------
#
# "Private"  methods
#
# ------------------------------------------------------------------------------


    # Try to get config parameter - wraps the exception handling for get_config_parameter()
    def try_get_config_param(self, services, param_name, optional=False):

        try:
            value = services.get_config_param(param_name)
            print param_name, ' = ', value
        except Exception:
            if optional:
                print 'config parameter ', param_name, ' not found'
                value = None
            else:
                message = 'required config parameter ', param_name, ' not found'
                print message
                services.exception(message)
                raise

        return value

    # Try to get component specific config parameter - wraps the exception handling
    def try_get_component_param(self, param_name, optional=False):

        if hasattr(self, param_name):
            value = getattr(self, param_name)
            print param_name, ' = ', value
        elif optional:
            print 'optional config parameter ', param_name, ' not found'
            value = None
        else:
            message = 'required component config parameter ', param_name, ' not found'
            print message
            services.exception(message)
            raise

        return value