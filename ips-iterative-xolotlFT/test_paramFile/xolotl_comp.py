#! /usr/bin/env python

from  component import Component
import os
import shutil
import subprocess
import glob
import xolotl_param_handler #write_xolotl_paramfile
import sys
import numpy as np

class xolotlWorker(Component):
    def __init__(self, services, config):
        Component.__init__(self, services, config)
        print 'Created %s' % (self.__class__)
        

    def init(self, timeStamp=0.0, **keywords):
        print('xolotl_worker: init')
        self.services.stage_plasma_state()

        print 'check that all arguments are read well by xolotl-init' 
        for (k, v) in keywords.iteritems():
            print '\t', k, " = ", v

        #asign a local variable to arguments used multiple times 
        self.driverTime=keywords['dTime']
        self.coupling=keywords['xFtCoupling']

        cwd = self.services.get_working_dir()

        xp = xolotl_param_handler.xolotl_params()
        xp.parameters=keywords['xParameters'] 

        print 'this is a test: the parameter dictionary is \n', xp.parameters

        print 'this is a test: the type of petsc arguments'
        for k,v in xp.parameters['petscArgs'].iteritems():
            print 'argument and type of', k , ' are ', v , ' and ', type(v)

        #test accessing xParamters
        #print 'this is a test: running Xolotl in ', xp.parameters['dimensions'], 'D' #input_parameters['dimensions'], 'D'

        #write and store xolotls parameter for each loop 
        xp.write('params.txt')
        currentXolotlParamFile='params_%f.txt' %self.driverTime
        shutil.copyfile('params.txt',currentXolotlParamFile) 
        
        #copy the restart network file to the present directory
        #if keywords['dStartMode']=='RESTART':
        #    restartNetworkFile='../../restart_files/'+xp.parameters['networkFile']
        #    shutil.copyfile(restartNetworkFile,xp.parameters['networkFile'])

        self.services.update_plasma_state()

    def step(self, timeStamp=0.0,**keywords):
        print('xolotl_worker: step')

        self.services.stage_plasma_state()

        #asign a local variable to arguments used multiple times

        print 'check that all arguments are read well by xolotl-step'
        for (k, v) in keywords.iteritems():
            print '\t', k, " = ", v
            
        zipOutput=keywords['dZipOutput']
        petscHeConc=keywords['xHe_conc']

        xolotlLogFile='xolotl_t%f.log' %self.driverTime
        print ('Xolotl log file ', xolotlLogFile)

        #call shell script that runs Xolotl and pipes input file
        task_id = self.services.launch_task(self.NPROC,
                                            self.services.get_working_dir(),
                                            self.XOLOTL_EXE, 'params.txt', 
                                            logfile=xolotlLogFile)

        #monitor task until complete
        if (self.services.wait_task(task_id)):
            self.services.error('xolotl_worker: step failed.')

        newest = max(glob.iglob('TRIDYN_*.dat'), key=os.path.getctime)
        print('newest file ' , newest)
        shutil.copyfile(newest, 'last_TRIDYN.dat')


        #save TRIDYN_*.dat files, zipped
        TRIDYNFiles='TRIDYN_*.dat'

        if self.coupling=='True' and zipOutput=='True':
            print 'this is a test: coupling and zipOutput are identified as boolean True and True'
            TRIDYNZipped='allTRIDYN_t%f.zip' %self.driverTime
            zip_ouput='zipTridynDatOuput.txt'

            print 'save and zip output: ', TRIDYNFiles
            zipString='zip %s %s >> %s ' %(TRIDYNZipped, TRIDYNFiles, zip_ouput)
            subprocess.call([zipString], shell=True)

            rmString='rm '+ TRIDYNFiles
            subprocess.call([rmString], shell=True)

        elif self.coupling=='True':
            print 'this is a test: coupling and zipOutput are identified as boolean True and False'
            print 'leaving ',  TRIDYNFiles , 'uncompressed'

        else:
            print 'this is a test: coupling and zipOutput are identified as boolean False and False'
            print 'no ', TRIDYNFiles , ' generated in this simulation'

        #save helium concentration files, zipped
        heConcFiles='heliumConc_*.dat'

        if petscHeConc and zipOutput=='True':
            print 'this is a test: heConc and zipOutput are identified as boolean True and True'
            heConcZipped='allHeliumConc_t%f.zip' %self.driverTime
            zip_ouput='zipHeConcOuput.txt'
            
            print 'save and zip output: ', heConcFiles
            zipString='zip %s %s >> %s ' %(heConcZipped, heConcFiles, zip_ouput)
            subprocess.call([zipString], shell=True)

            rmString='rm '+heConcFiles
            subprocess.call([rmString], shell=True)
            
        elif petscHeConc:
            print 'this is a test: heConc and zipOutput are identified as boolean True and False'
            print 'leaving ', heConcFiles ,'uncompressed'

        else:
            print 'this is a test: heConc and zipOutput are identified as boolean False and False'
            print 'no ', heConcFiles , ' in this loops output'

        #save network file with a different name to use in the next time step
        currentXolotlNetworkFile='xolotlStop_%f.h5' %self.driverTime
        shutil.copyfile('xolotlStop.h5',currentXolotlNetworkFile)

        statusFile=open(self.EXIT_STATUS, "r")
        exitStatus=statusFile.read().rstrip('\n')

        if exitStatus=='collapsed':
            print 'simulation exited loop with status collapse'
            print 'rename output files as _collapsed before trying again'

            currentXolotlNetworkFile='xolotlStop_%f.h5' %self.driverTime
            networkFile_unfinished='xolotlStop_%f_collapsed.h5' %self.driverTime
            os.rename(currentXolotlNetworkFile,networkFile_unfinished)

            retentionFile = self.RET_FILE
            rententionUnfinished = 'retention_t%f_collapsed.out' %self.driverTime
            shutil.copyfile(retentionFile,rententionUnfinished)
            
            surfaceFile=self.SURFACE_FILE
            surfaceUnfinished='surface_t%f_collapsed.txt' %self.driverTime
            shutil.copyfile(surfaceFile,surfaceUnfinished)

            if zipOutput=='True':
                TRIDYNZipped='allTRIDYN_t%f.zip' %self.driverTime
                TRIDYNUnfinished='allTRIDYN_t%f_collapsed.zip' %self.driverTime
                os.rename(TRIDYNZipped,TRIDYNUnfinished)
                if petscHeConc:
                    heConcZipped='allHeliumConc_t%f.zip' %self.driverTime
                    heConcUnfinished='allHeliumConc_t%f_collapsed.zip' %self.driverTime
                    os.rename(heConcZipped,heConcUnfinished)
            
        #updates plasma state Xolotl output files
        self.services.update_plasma_state()
  
    def finalize(self, timeStamp=0.0):
        return
    
