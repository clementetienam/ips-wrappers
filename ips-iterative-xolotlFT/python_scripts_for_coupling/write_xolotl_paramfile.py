#!/usr/bin/env python
#=======================================================================================
# write_xoltol_paramfile.py
# writes the parameter file for xolotl (outputfile), replacing variable values (tmax, network file, sputtering yield) in the input file (infile)
#=======================================================================================

import os
import subprocess


def writeXolotlParameterFile_fromTemplate(infile="paramXolotlTemplate.txt", outfile="params.txt",

                                          start_stop=True,
                                          start_stop_time=0.2,
                                          #ts_dt_time=0.2, #obsolete
                                          force_iteration=False,
                                          ts_adapt_monitor=False,
                                          ts_final_time=0.2,
                                          ts_max_snes_failures=-1,
                                          ts_max_steps=1000000,
                                          ts_exact_final_time="matchstep",
                                          ts_adapt_dt_max=1.0e-5,
                                          ts_monitor=True,
                                          
                                          fieldsplit_0_pc_type="sor",
                                          fieldsplit_1_pc_type="redundant",

                                          pc_fieldsplit_detect_coupling=True,
                                          pc_type="fieldsplit",

                                          check_collapse=True,
                                          exit_threshold=1.0e-16,

                                          vizHandler="dummy",
                                          flux=4.0e4,
                                          material="TRIDYN",
                                          dimensions=1,
                                          perfHandler="dummy",
                                          startTemp=773,
                                          process="reaction advec modifiedTM attenuation diff movingSurface",
                                          sputtering=0.000129,
                                          voidPortion=40,
                                          boundarySurf=1, #1=free
                                          boundaryBulk=0, #0=reflective
                                          
                                          #   netParam=nHe maxVSize  nInterstitials phaseCut
                                          #   grid=nxGrid dxGrid
                                          useNetFile=False,
                                          networkFile="xolotlStop.h5",                                          
                                          nHe=8,
                                          maxVSize=250, 
                                          nInterstitials=6, 
                                          phase_cut='true',
                                          nxGrid=160,
                                          dxGrid=0.5,
                                          nyGrid=' ',
                                          dyGrid=' ',

                                          #bursting=False,
                                          grouping=False,
                                          groupHeV=0,
                                          groupHe=0,
                                          groupV=0,

                                          initialV=0.0,
                                          
                                          he_conc=True
                                          ):
   tmp="temp.txt"
#   ftmp=open("temp.txt", "w")                                                                                                                                                                
   if (infile==outfile):
      os.rename(infile, tmp)
      infile=tmp

# prepare petscline:                                                                                                                                                                          

   #change of value in parameters                                                                                                                                                             
   petscArgString=" -e 's/-ts_final_time [^ ]*/-ts_final_time %f/'   -e 's/-ts_max_snes_failures [^ ]*/-ts_max_snes_failures %d/'   -e 's/-ts_max_steps [^ ]*/-ts_max_steps %d/'   -e 's/-ts_exact_final_time [^ ]*/-ts_exact_final_time %s/'   -e 's/-ts_adapt_dt_max [^ ]*/-ts_adapt_dt_max %e/'   -e 's/-fieldsplit_0_pc_type [^ ]*/-fieldsplit_0_pc_type %s/'   -e 's/-fieldsplit_1_pc_type [^ ]*/-fieldsplit_1_pc_type %s/'   -e 's/-pc_type [^ ]*/-pc_type %s/' "  % (ts_final_time, ts_max_snes_failures, ts_max_steps, ts_exact_final_time, ts_adapt_dt_max, fieldsplit_0_pc_type, fieldsplit_1_pc_type, pc_type)

   #include (or not) parameters without values that exist in template file
   if not start_stop: #(start_stop==False):
      petscArgString=petscArgString+"   -e 's/-start_stop [^ ]*/ /'"
      #petscArgString=petscArgString+"   -e 's/-ts_dt [^ ]*/ /'" #obsolete
   else:
      petscArgString=petscArgString+"   -e 's/-start_stop [^ ]*/-start_stop %f/'" %(start_stop_time)
      #petscArgString=petscArgString+"   -e 's/-ts_dt [^ ]*/-ts_dt %f/'" %(ts_dt_time) #obsolete


   if not force_iteration: #(force_iteration==False): remove from petsc arguments            
      petscArgString=petscArgString+"   -e 's/-snes_force_iteration [^ ]*/ /'"

   if not ts_adapt_monitor: #(ts_adapt_monitor==false) remove from petsc arguments
      petscArgString=petscArgString+"   -e 's/-ts_adapt_monitor [^ ]*/ /'"
      print 'ts_adapt not monitored'
   else:
      print 'ts_adapt IS MONITORED'

   if not check_collapse:
      petscArgString=petscArgString+"   -e 's/-check_collapse [^ ]*/ /'"
   else:
      petscArgString=petscArgString+"   -e 's/-check_collapse [^ ]*/-check_collapse %e/'" %(exit_threshold)

   if not he_conc:# (he_conc==False):
      #print 'he conc False; not included in param file'
      petscArgString=petscArgString+"   -e 's/-helium_conc/ %s/'" %( ' ' )


   #prepare sed line                                                                                                                                                                          
   petscArgSedString="sed "+ petscArgString + "< %s > %s" %(infile , outfile)
   #print 'TEST:  running Sed String: ',petscArgSedString

   #run sed line for Petsc                                                                                                                                                                    
   subprocess.call([petscArgSedString], shell=True)

   #other input parameters
   os.rename(outfile, tmp)
   paramSedString="sed    -e 's/vizHandler=[^ ]*/vizHandler=%s/'    -e 's/flux=[^ ]*/flux=%e/'    -e 's/netParam=.*$/netParam=%g %g %g %s/'   -e 's/grid=.*$/grid=%g %g %s %s/'    -e 's/material=[^ ]*/material=%s/'    -e 's/dimensions=[^ ]*/dimensions=%d/'    -e 's/perfHandler=[^ ]*/perfHandler=%s/'    -e 's/startTemp=[^ ]*/startTemp=%f/'   -e 's/sputtering=[^ ]*/sputtering=%f/'  -e 's/voidPortion=[^ ]*/voidPortion=%f/'   -e 's/initialV=[^ ]*/initialV=%g/' -e 's/boundary=.*$/boundary=%d %d/' -e 's/process=.*$/process=%s/' < %s > %s"   % (vizHandler, flux, nHe, maxVSize, nInterstitials, phase_cut, nxGrid, dxGrid , nyGrid, dyGrid, material, dimensions, perfHandler, startTemp, sputtering, voidPortion, initialV, boundarySurf, boundaryBulk, process, tmp, outfile)

   #print " sedline call parameters: %s " %(paramSedString)                                                                                                                                   
   subprocess.call([paramSedString], shell=True)

#append other input parameters that do not exist in preprocessors param file
   f = open(outfile, "a")

   if useNetFile:
      networkFileLine="networkFile=%s\n" %(networkFile)
      f.write(networkFileLine)

   if grouping:
      groupingFileLine="grouping=%g %g %g\n" %(groupHeV, groupHe, groupV)
      f.write(groupingFileLine)

   f.close

   os.remove(tmp)

   return


################# END OF NEW PYTHON SCRIPT (v3) ####################

if __name__ == '__main__':

   import shutil

   writeXolotlParameterFile_fromPreprocessor()

   shutil.copyfile("params.txt", "params1.txt")

   writeXolotlParameterFile_fromTemplate(start_stop=0.02,ts_final_time=0.02,networkFile="xolotlStop.h5",sputtering=0.1)

   shutil.copyfile("params.txt", "params2.txt")
