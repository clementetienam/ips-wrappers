#! /usr/bin/env python

#-------------------------------------------------------------------------------
#
#  IPS wrapper for SOLPS-ITER_init component. Take the work flow inputs and
#  generates a plasma state.
#
#-------------------------------------------------------------------------------

from component import Component
import os
from utilities import ZipState

#-------------------------------------------------------------------------------
#
#  SOLPS-ITER_init Component Constructor
#
#-------------------------------------------------------------------------------
class solps_iter_init(Component):
    def __init__(self, services, config):
        print('solps_iter_init: Construct')
        Component.__init__(self, services, config)

#-------------------------------------------------------------------------------
#
#  SOLPS-ITER_init Component init method. This method prepairs the input files.
#  This allows staging the plasma state files.
#
#-------------------------------------------------------------------------------
    def init(self, timeStamp=0.0):
        print('solps_iter_init: init')

#  Get config filenames.
        current_solps_state = self.services.get_config_param('CURRENT_SOLPS_STATE')
        eirene_input_dat = self.services.get_config_param('EIRENE_INPUT_DAT')
        eirene_nodes = self.services.get_config_param('EIRENE_NODES')
        eirene_cells = self.services.get_config_param('EIRENE_CELLS')
        eirene_links = self.services.get_config_param('EIRENE_LINKS')

#  Stage input files. Remove old namelist input if it exists.
        if os.path.exists(current_solps_state):
            os.remove(current_solps_state)
        if os.path.exists('fort.1'):
            os.remove('fort.1')
        if os.path.exists('fort.33'):
            os.remove('fort.33')
        if os.path.exists('fort.34'):
            os.remove('fort.34')
        if os.path.exists('fort.35'):
            os.remove('fort.35')
        if os.path.exists(eirene_input_dat):
            os.remove(eirene_input_dat)
        if os.path.exists(eirene_nodes):
            os.remove(eirene_nodes)
        if os.path.exists(eirene_cells):
            os.remove(eirene_cells)
        if os.path.exists(eirene_links):
            os.remove(eirene_links)
        if os.path.exists('b2fgmtry'):
            os.remove('b2fgmtry')
        if os.path.exists('b2fpardf'):
            os.remove('b2fpardf')
        if os.path.exists('b2frates'):
            os.remove('b2frates')
        if os.path.exists('b2fstati'):
            os.remove('b2fstati')
        if os.path.exists('b2mn.dat'):
            os.remove('b2mn.dat')
        if os.path.exists('b2.transport.parameters'):
            os.remove('b2.transport.parameters')
        if os.path.exists('b2.numerics.parameters'):
            os.remove('b2.numerics.parameters')
        if os.path.exists('b2.neutrals.parameters'):
            os.remove('b2.neutrals.parameters')
        if os.path.exists('b2.boundary.parameters'):
            os.remove('b2.boundary.parameters')
    
        self.services.stage_input_files(self.INPUT_FILES)

#  Rename the eirene input files.
        os.rename(eirene_input_dat, 'fort.1')
        os.rename(eirene_nodes, 'fort.33')
        os.rename(eirene_cells, 'fort.34')
        os.rename(eirene_links, 'fort.35')

#  Create plasma state zip file.
        with ZipState.ZipState(current_vmec_state, 'a') as zip_ref:

#  b2 files
            zip_ref.write('b2fgmtry')
            zip_ref.write('b2fpardf')
            zip_ref.write('b2frates')
            zip_ref.write('b2fstati')
            zip_ref.write('b2mn.dat')

            zip_ref.write('b2.transport.parameters')
            zip_ref.write('b2.numerics.parameters')
            zip_ref.write('b2.neutrals.parameters')
            zip_ref.write('b2.boundary.parameters')

#  eirene files
            zip_ref.write('fort.1')
            zip_ref.write('fort.33')
            zip_ref.write('fort.34')
            zip_ref.write('fort.35')

            zip_ref.set_state(state='needs_update')

        self.services.update_plasma_state()

#-------------------------------------------------------------------------------
#
#  SOLPS-ITER_init init Component step method. This runs vmec.
#
#-------------------------------------------------------------------------------
        def step(self, timeStamp=0.0):
            print('solps_iter_init: step')
    
#-------------------------------------------------------------------------------
#
#  SOLPS-ITER_init init Component finalize method. This cleans up afterwards. Not used.
#
#-------------------------------------------------------------------------------
        def finalize(self, timeStamp=0.0):
            print('solps_iter_init: finalize')