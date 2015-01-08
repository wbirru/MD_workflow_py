#!/usr/bin/env python
# MD workflow functions.   mdwf 
""" mdwf functions.                    version 0.25
"""

import os
import subprocess
import sys 
from   collections import OrderedDict
import json
import shutil
import fileinput
import hashlib
import time 
import datetime
import glob
import re

# ansi color variables for formatting purposes: 
c0 = '\033[0m'        # default
c1 = '\033[31;2m'     # dark red 
cc1 = '\033[0m'        # default
c10= '\033[2m'        # grey 
c2 = '\033[32;1m'     # light green
c3 = '\033[32;2m'     # dark green
c4 = '\033[33;1m'     # light yellow
c5 = '\033[0m'           # spring green
c6 = '\033[34;1m'     # light blue
c7 = '\033[34;2m'     # dark blue
c8 = '\033[38;5;220m' # orange 
c9 = '\033[36;1m'     # cyan

#Testing individual functions started 12/12/2014 EB branch file

def read_master_config_file():  
    """ Reads parameters from 'master_config_file'  """  
    if os.path.isfile( 'master_config_file' ):
        master_json = open( 'master_config_file' )
        try: 
            mcf = json.load(master_json,object_pairs_hook=OrderedDict)
            master_json.close()
        except:
            print "\nPossible .json format errors of {}'master_config_file'{}\n".format(c1,c0)
    else:
        print "{}Can't see 'master_config_file' in directory:{} {}\n".format(c1,cwd,c0) 
        print "{}Have you populated the directory? (./mdwf -p){} \n".format(c1,c0) 
        sys.exit()
    return mcf

def read_local_job_details_file(path="Setup_and_Config",ljdf_target="local_job_details_template.json"):  
    """ Reads parameters from local job details file """  
    # default target  /Setup_and_Config/local_job_details_template.json"
    target = path + "/" + ljdf_target
    if os.path.isfile(target):
        local_json = open(target)
        try: 
            ljdf = json.load(local_json,object_pairs_hook=OrderedDict)
            local_json.close()
        except:
            error = "\nPossible .json format errors of {}".format(target)
            sys.exit(error)
    else:
        error = "Can't see {} ".format(target) 
        sys.exit(error)
  
    return ljdf

def read_namd_job_details(targetfile):
    """ Extracts simulation details from given namd config file and returns a dictionary. """
    # assumes files are located in /Setup_and_Config 
    target = os.getcwd() + "/Setup_and_Config/" + targetfile
    jdd = {}      # job-details dictionary  
    jdpl = []     # job details parameter list

    if os.path.isfile(target):
        f = open(target,'r')
        for lline in f:
            line = lline[0:18]          # strip line to avoid artifacts
            if not "#" in line[0:2]:    # leave out commented lines
                if 'structure ' in line:
                    pl = lline.split()
                    jdd[ "psffilepath" ] = pl[1]
                    nl = re.split(('\s+|/|'),lline)
                    for i in nl:
                        if '.psf' in i:
                            jdd[ "psffile" ] = i
                            natom = estimate_dcd_frame_size(i)        
                            jdd[ "natom" ] = natom

                if 'coordinates ' in line:
                    pl = lline.split()
                    jdd[ "pdbfilepath" ] = pl[1]
                    nl = re.split(('\s+|/|'),lline)
                    for i in nl:
                        if '.pdb' in i:
                            jdd[ "pdbfile" ] = i

                if 'timestep ' in line:
                    nl = lline.split()
                    jdd[ "timestep" ] = nl[1]

                if 'NumberSteps ' in line:
                    nl = lline.split()
                    jdd[ "steps" ] = nl[2]

                if 'dcdfreq ' in line:
                    nl = lline.split()
                    jdd[ "dcdfreq" ] = nl[1]

                if 'run ' in line:
                    nl = lline.split()
                    jdd[ "runsteps" ] = nl[1]

                if 'restartfreq ' in line:
                    nl = lline.split()
                    jdd[ "restartfreq" ] = nl[1]

                if 'parameters ' in line:
                    nl = lline.split()
                    jdpl.append(nl[1])
        f.close()
    else: 
        print "{} {} file not found.{}".format(c1,targetfile,c0)
    return jdd, jdpl

def estimate_dcd_frame_size(psffile):
    """ function to estimate dcd frame size of simulation based on the numbers of atoms. """
#   assumes psf file is in /InputFiles directory. 
    target=os.getcwd() + "/InputFiles/" + psffile
    atoms = 0 
    if os.path.isfile(target):
        f = open(target,'r')
        for line in f:
            if 'NATOM' in line:     # extract number of atoms from !NATOM line
                nl = line.split()
                atoms = nl[0]
        f.close()    
    else:
        print "{}Can't find {} in /InputFiles directory {}".format(c1,psffile,c0)
    return atoms

def check_for_pausejob():
    """checks for pausejob flag in local job details file"""
    status = "go"
    if os.path.isfile('pausejob'):
        error = "\nPausejob flag present. Stopping job.\n" 
        status = "Stopped: Pausejob flag present"
        key    = "JobStatus"
        update_local_job_details( key, status )
        sys.exit(error)
    return status

def create_pausejob_flag(error):
    """create pausejob flag to initiate a soft job stop """
    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y_%h_%d_%H:%M')

    with open('pausejob', 'w+') as pausejob:
        pausejob.write(timestamp + "\n" + (error) + "\nBe sure to delete pausejob before continuing your simulation.")
    pausejob.close()

def initialize_job_countdown(equilib = "single"):
    """intializes rounds and countdown timers of local details file based on master_config_file"""
    # equilib represents equilibration strategy:
    # "single" for one equilibration that is then passed to all other job directories. 
    # or "multiple" for each job directory starting its own unique equilibration phase.
    return


def check_disk_quota(account,diskcutoff):
    """ function for checking that there is enough diskspace on the system before starting job"""
# run a local systems script "mydisk"  and extract the information    
    try:
        disk = subprocess.check_output('mydisk')
        dline = disk.split("\n")
        for i in dline:
            if account in i:               # looks for the line with the matching account number
                usage = i.split()[-1][:-1] # extracts last 'word' of matching line cutting of '%'
        a = int(usage)
        b = int(diskcutoff)
        if (a>b):
            print "Warning: Account {} disk space quota low. Usage: {} % ".format(account,a)          
            error = "\nDiskspace too low. usage: {}%  disk limit set to: {}%\n".format(a,b) 
            ljdf[ "PauseJobFlag" ] = "1"
            status = "Stopped: Disk quota too low."
            key = "JobStatus"
            update_local_job_details( key, status )
            status = "Stopped: Disk quota too low."
            key = "JobMessage"
            update_local_job_details( key, status )


            sys.exit(error)
    except:
        print "Can't run 'mydisk' on system. Can't check disk quota for account {}.".format(account) 

    return

def log_job_details(jobid):
    """logging cluster job details"""
# update job details
    ljdf[ "CurrentJobId" ] = jobid
    try:
        jobdetails = subprocess.check_output([ "scontrol", "show", "job", str(jobid)])
        jdsplit = re.split(' |\n', jobdetails)  
# add details to local job details file:
        for i in jdsplit:
            if "JobState=" in i:
                ljdf[ "JobStatus" ]    = i.split("=")[1]
            if "NumNodes=" in i:
                ljdf[ "Nodes" ]        = i.split("=")[1]
            if "NumCPUs=" in i:
                ljdf[ "Cores" ]        = i.split("=")[1]
            if "StartTime=" in i:
                ljdf[ "JobStartTime" ] = i.split("=")[1]
            if "TimeLimit=" in i:
                ljdf[ "WallTime" ]     = i.split("=")[1]
    except:
        print" "


def record_start_time():
    """ to log start time in unix time to local details"""
    starttime = int(time.time())
    try:
        ljdf[ "JobStartTime" ] = starttime
    except:
        print "\ncan't write start time to local job detail file.\n"

def record_finish_time():
    """ to log start time in unix time to local details"""
    finishtime = int(time.time())
    try:
        ljdf[ "JobFinishTime" ] = finishtime
    except:
        print "\ncan't write finish time to local job detail file.\n"

def check_job_fail(start,finish,limit):
    """ check for job failure """
    runtime = finish - start
    if runtime < limit:
        error = "Job ran shorter than expected. Possible crash."
        status = "Short run time: crash? Stopped Job"
        key = "JobStatus"
        update_local_job_details( key, status )
        create_pausejob_flag(error)
        sys.exit(error)

def check_run_count(current,total):
    """ fail safe to prevent excessive unwanted simulations from occurring """
    if total - current < 0:
        error = "I'm sorry, Dave. I'm afraid I can't do that."
        status = "An error has occured and an unwanted number of jobs are being created"
        create_pausejob_flag(status)
        sys.exit(error)

def check_final_run(current,total):
    """ end simulation at the completion of final run """
    if total - current <= 0:
        error = "All runs completed"
        status = "All runs completed"
        create_pausejob_flag(error)
        final_run_cleanup()

def final_run_cleanup():
    """ job directory will be cleaned following the final run """
    for file in glob.glob("FFTW*"):
        shutil.move(file, "OutputText/")
    for file in glob.glob("*.BAK"):
        os.remove(file)
    for file in glob.glob("generic_restartfile*"):
        os.remove(file)
    for file in glob.glob("temporary*"):
        os.remove(file)
    for file in glob.glob("Temp*"):
        os.remove(file)    

def log_job_timing():
    """ log length of job in human readable format """
#  still to do


def create_job_basename(name, run):
    """ creates a time stamped basename for current job"""
    ts = time.time()
    stamp = datetime.datetime.fromtimestamp(ts).strftime('%Y_%h_%d_%H%S_')
    basename = stamp + name + "_r_" + run
    return basename

def update_local_job_details(key, status):
    """ updates local job details of 'local job details file' """
    ljdf_t = read_local_job_details_file(".", "local_job_details.json")
    try:
        ljdf_t[key] = status
        with open("local_job_details.json", 'w') as outfile:
            json.dump(ljdf_t, outfile, indent=2)
        outfile.close()
    except:
        print "Can't update local job details file."

def redirect_output(name, run, CurrentWorkingFile="current_MD_run_files"):
    """ A function to redirect NAMD output to various locations."""

  # create a base name based on passed arguments name and run.
    try:
        basename = create_job_basename(name, run)
    except:
        error = "\nError making basename. (In redirect_output function) "
        sys.exit(error)

 # make shorthand of current working files
    cwf_coor = CurrentWorkingFile + ".coor"
    cwf_vel  = CurrentWorkingFile + ".vel"
    cwf_xsc  = CurrentWorkingFile + ".xsc"
    cwf_xst  = CurrentWorkingFile + ".xst"
    cwf_dcd  = CurrentWorkingFile + ".dcd"

 # copy CurrentWorking (restart) files to LastRestart/ directory 
    try:
        shutil.copy (cwf_coor, 'LastRestart/' + cwf_coor)
        shutil.copy (cwf_vel,  'LastRestart/' + cwf_vel)
        shutil.copy (cwf_xsc,  'LastRestart/' + cwf_xsc)
    except:	
        error = "\nError moving restart files to /LastRestart (In redirect_output function) "
        sys.exit(error)

 # rename and move current working files
    try: 
        os.rename (cwf_dcd,  'OutputFiles/' + basename + cwf_dcd)
        os.rename (cwf_vel,  'OutputFiles/' + basename + cwf_vel)
        os.rename (cwf_xsc,  'OutputFiles/' + basename + cwf_xsc)
        os.rename (cwf_xst,  'OutputFiles/' + basename + cwf_xst)
        os.rename (cwf_coor, 'OutputFiles/' + basename + cwf_coor)
    except:	
        error = "\nError moving files to /OutputFiles (In redirect_output function) "
        sys.exit(error)

 # clean up remaining files
    post_job_clean()

    return

def post_job_clean():
    """ remove unwanted error, backup files, etc """
    for file in glob.glob("slurm*"):
        shutil.move(file, "JobLog/")
    for file in glob.glob("core*"):
        shutil.move(file, "Errors/")
    return

def countdown_timer():
    """ function to adjust countdown timer """
## still to do 

def check_if_job_running():
    """ function to check if job already running in current working directory """ 
    dir_path = os.getcwd()
    # read status from local job details file
    ljdf_t = read_local_job_details_file(dir_path, "local_job_details.json") 
    current_jobid     = ljdf_t[ "CurrentJobId" ]
    current_jobstatus = ljdf_t[ "JobStatus" ]
## needs efficient way to check queue
    return current_jobstatus, current_jobid

def monitor_jobs():
    """ -function to monitor jobs status on the cluster """ 
    mcf = read_master_config_file()
    cwd = os.getcwd()
    try:
        JobStreams, Replicates, BaseDirNames, JobBaseNames, Runs, nJobStreams, nReplicates, nBaseNames = check_job_structure() 
    except: 
        sys.stderr.write("Trouble reading job structure from 'master_config_file' ")
    Account = mcf[ "Account" ]

    #jobdirlist = get_curr_job_list(JobDir)

    print "Job Name:      |Progress: |JobId:    |Status:   |Nodes:  |Walltime: |Job_messages:"
    print "---------------|----------|----------|----------|--------|----------|------------------ "

    for i in range(0,nJobStreams): 
        JobDir = JobStreams[i]
        jobdirlist = get_current_dir_list(JobDir) 
        print c2 + JobDir + ":"+ c0
        for j in jobdirlist:  
	    dir_path = JobDir + "/" + j  
            ljdf_t = read_local_job_details_file(dir_path, "local_job_details.json") 
            jdn  = ljdf_t[ "JobDirName" ]
            qs   = ljdf_t[ "QueueStatus" ]
            js   = ljdf_t[ "JobStatus" ]
            jm   = ljdf_t[ "JobMessage" ]
            nodes= ljdf_t[ "Nodes" ]
            wt   = ljdf_t[ "Walltime" ]
            cjid = str(ljdf_t[ "CurrentJobId" ])
            #prog = str(ljdf_t[ "CurrentJobRound" ] + ": " + ljdf_t[ "RunCountDown" ] + "/" + ljdf_t[ "TotalRuns" ]) 
            prog =  ljdf_t[ "CurrentRun" ] + "/" + ljdf_t[ "TotalRuns" ] 
            print "%-16s %8s %10s %10s %8s %10s   %12s" % (jdn[0:11], prog, cjid, js, nodes, wt, jm) 

    print "{}done.".format(c0)

def md5sum(filename, blocksize=65536):
    """function for returning md5 checksum"""
    hash = hashlib.md5()
    with open(filename, "r+b") as f:
        for block in iter(lambda: f.read(blocksize), ""):
            hash.update(block)
        f.close()
    return hash.hexdigest()

def getfilesize(filename):
    size = os.path.getsize(filename)
    return size

def check_job_structure():
    """ Function to check job structure in 'master_config_file' """
    # This reads the job structure file, check consistency. 
    mcf = read_master_config_file()
    try:                  
        JobStreams   = mcf[ "JobStreams" ]
        Replicates   = mcf[ "JobReplicates" ] 
        BaseDirNames = mcf[ "BaseDirNames" ]     
        JobBaseNames = mcf[ "JobBaseNames" ]     
        Runs         = mcf[ "Runs" ]     
    except: 
        error = "Error reading master_config_file variables while initializing job directories."
        sys.exit(error)

    # check that job details lists are the same length in master_config_file: 
    try:
        nJobStreams   = int( len( JobStreams )) 
        nReplicates   = int( len( Replicates ))
        nBaseNames    = int( len( BaseDirNames ))
        nJobBaseNames = int( len( JobBaseNames ))
        nRuns         = int( len( Runs ))
    except:
        error = "Error reading Job Details Section in master_config_file."
        sys.exit(error) 
    if not nJobStreams==nReplicates==nBaseNames==nJobBaseNames==nRuns:
        error = "Job Details Section lists do not appear to be the same length in master_config_file." 
        sys.exit(error) 
    return JobStreams, Replicates, BaseDirNames, JobBaseNames, Runs, nJobStreams, nReplicates, nBaseNames

def initialize_job_directories():
    """ Function to setup job structure directories as defined in the 'master_config_file'"""
    cwd=os.getcwd()
    try:
        JobStreams, Replicates, BaseDirNames, JobBaseNames, Runs, nJobStreams, nReplicates, nBaseNames = check_job_structure() 
    except: 
        error = "Trouble passing job structure variables."
        sys.exit(error)

    # create job stream structure:  /JobStreams/JobReplicates
    for i in range(0, nJobStreams):
        TargetJobDir = cwd + "/" + JobStreams[i]
        if not os.path.exists(TargetJobDir):
            print "Job Stream directory /{} does not exist. Making new directory.".format(TargetJobDir)
            try:
                os.makedirs(JobStreams[i]) 
            except:
                error = "Error making directory in /{}.".format(cwd)
                sys.exit(error) 

        # Copy directory structure from /Setup_and Config/JobTemplate
        print "Making job replicates in /{}".format(JobStreams[i])
        TemplatePath = cwd + "/Setup_and_Config/JobTemplate"

        # check existance of JobTemplate directory:
        if not os.path.exists(TemplatePath):
            error = "Can't find the /Setup_and_Config/JobTemplate directory. Exiting."
            sys.exit(error) 

        replicates = int(Replicates[i])
        zf = len(str(replicates)) + 1     # z fill for numbering replicate directories 

        for j in range(1,replicates+1):
            suffix = str(j).zfill(zf)
            NewDirName = JobStreams[i] + "/" + BaseDirNames[i] + suffix 
         
            if os.path.exists(NewDirName):
                print "Replicate job directory {} already exists! -Skipping.".format(NewDirName) 
            else:
                try: 
                    shutil.copytree(TemplatePath, NewDirName)
                    print "Creating:{}".format(NewDirName)             
                except: 
                    print "Error in creating replicate directory."

def populate_job_directories():
    """ -function to populate or update job directory tree with job scripts """
#   # checking job structure as defined in 'master_config_file':
    try:
        JobStreams, Replicates, BaseDirNames, JobBaseNames, Runs, nJobStreams, nReplicates, nBaseNames = check_job_structure() 
    except: 
        error = "Trouble passing job structure variables."
        sys.exit(error)

#   # reading information from master_config_file and local job details template:
    mcf    = read_master_config_file()
    ljdf_t = read_local_job_details_file()
    cwd=os.getcwd()

    try:
        Flavour          = mcf[ "Flavour" ]
        Round            = mcf[ "Round" ]
        Account          = mcf[ "Account" ]
        Nodes            = mcf[ "nodes" ]
        Ntpn             = mcf[ "ntpn" ]
        Ppn              = mcf[ "ppn" ]
        OptScript        = mcf[ "EquilibrateConfScript" ]
        ProdScript       = mcf[ "ProductionConfScript" ]
        ModuleFile       = mcf[ "ModuleFile" ]
        Walltime         = mcf[ "Walltime" ]
        startscript      = mcf[ "SbatchEquilibrateScript" ]
        productionscript = mcf[ "SbatchProductionScript" ]
        dsco             = mcf[ "DiskSpaceCutOff" ]
        jft              = mcf[ "JobFailTime" ]
    except:
        error = "Error reading master_config_file variables during populate routine"
        sys.exit(error)

#   # create local job detalis staging file from ljdf_template
    stagef = ljdf_t           

#   # modify common elements in staging dictionary file:
    stagef[ 'TOP_DIR' ]         = cwd
    stagef[ 'CurrentRound' ]    = Round
    stagef[ 'JobFailTime' ]     = jft
    stagef[ 'DiskSpaceCutOff' ] = dsco
    stagef[ 'BASE_DIR' ]        = cwd
    stagef[ 'CurrentRound' ]    = Round
    stagef[ 'Account' ]         = Account
    stagef[ 'Nodes' ]           = Nodes
    stagef[ 'ntpn' ]            = Ntpn
    stagef[ 'ppn' ]             = Ppn
    stagef[ 'Walltime' ]        = Walltime
    stagef[ 'JobFailTime' ]     = jft
    stagef[ 'DiskSpaceCutOff' ] = dsco


## list files to transfer:
    print "{}Job Files to transfer from /Setup_and_Config:{}".format( c2, c0 ) 
    print "{}  {} \n  {} ".format( c3, startscript, productionscript )
    for pyfile in glob.glob(r'Setup_and_Config/*.py' ):
        print "  " + pyfile[17:]    
    for conffile in glob.glob(r'Setup_and_Config/*.conf' ):
        print "  " + conffile[17:]  

## descend through job structure and populate job directories:
    for i in range(0, nJobStreams):
        TargetJobDir = cwd + "/" + JobStreams[i]
        print "{}\nPopulating JobStream: {} {}".format( c2, TargetJobDir, c0) 

## check to see if there actually are any job directories to fill:
        if not os.path.exists( TargetJobDir ):
            error = "Job directory {} not found. Have you initialized?".format(TargetJobDir)
            sys.exit(error)

## create temporary sbatch scripts:
        sb_start_template = "Setup_and_Config/" + startscript      + ".template"
        sb_prod_template  = "Setup_and_Config/" + productionscript + ".template"
        if not os.path.exists( sb_start_template ) or not os.path.exists( sb_prod_template ):
            error = "Can't find sbatch template files in Settup_and_Config. Exiting."
            sys.exit(error)

## modify replicate elements in staging dictionary file:
        stagef[ 'JOB_STREAM_DIR' ] = JobStreams[i]
        stagef[ 'CurrentRun' ]     = Runs[i]
        stagef[ 'TotalRuns' ]      = Runs[i]
        stagef[ 'JobBaseName' ]    = JobBaseNames[i]

        nnodes   = "#SBATCH --nodes="   + Nodes
        ntime    = "#SBATCH --time="    + Walltime
        naccount = "#SBATCH --account=" + Account
        nntpn    = "ntpn=" + Ntpn
        nppn     = "ppn="  + Ppn
        nmodule  = "module load " + ModuleFile
        nopt     = "optimize_script=" + OptScript
        nprod    = "production_script=" + ProdScript

        shutil.copy( sb_start_template, 'sb_start_temp')
        shutil.copy( sb_prod_template,  'sb_prod_temp' )

## replace lines in sbatch files:
        for f in [ "sb_start_temp", "sb_prod_temp" ]:
            for line in fileinput.FileInput( f, inplace=True ):
                line = line.replace( '#SBATCH --nodes=X', nnodes )   
                line = line.replace( '#SBATCH --time=X', ntime )   
                line = line.replace( '#SBATCH --account=X', naccount )   
                line = line.replace( 'ntpn=X', nntpn )   
                line = line.replace( 'ppn=X',  nppn )   
                line = line.replace( 'module load X', nmodule )   
                line = line.replace( 'optimize_script=X', nopt )   
                line = line.replace( 'production_script=X', nprod )   
                sys.stdout.write(line)   

## update local job details file:
        jobdirlist = get_current_dir_list( JobStreams[i] )
        for j in jobdirlist:
            print "{} -populating: {}{}".format( c3, j, c0 )
            stagef[ 'JobDirName' ] = j
            ljdfile = JobStreams[i] + "/" + j + "/local_job_details.json"

            with open(ljdfile, 'w') as outfile:
                json.dump(stagef, outfile, indent=2)
            outfile.close()

## copy across python scripts from /Setup_and_Config:
            jobpath  = JobStreams[i] + "/" + j + "/"
            sbs_path = jobpath       + "/" + startscript
            sbp_path = jobpath       + "/" + productionscript

            shutil.copy( 'sb_start_temp', sbs_path )
            shutil.copy( 'sb_prod_temp' , sbp_path )

            for pyfile in glob.glob(r'Setup_and_Config/*.py' ):
                try:
                    shutil.copy2( pyfile, jobpath )
                except:
                    print "Can't copy python scripts from /Setup_and_Config/"  

            for conffile in glob.glob(r'Setup_and_Config/*.conf' ):
                try:
                    shutil.copy2(conffile, jobpath)
                except:
                    print "Can't copy .conf scripts from /Setup_and_Config/"  

## remove tempfiles. 
    os.remove( 'sb_start_temp' )
    os.remove( 'sb_prod_temp' )
    print "\n -done populating directories"

def check_job():
    """ -function to check the input of the current job and calculate resources required."""
    mcf = read_master_config_file()
    jd_opt,  jd_opt_pl  = read_namd_job_details(mcf[ "EquilibrateConfScript" ])    
    jd_prod, jd_prod_pl = read_namd_job_details(mcf[ "ProductionConfScript" ])    
    sr = 0             # Initalise no. of job repliates
    run = 0            # Initalise no. of runs in each replicate
    print "{}\nJob check summary: ".format(c1)
    print "{}--------------------------------------------------------------------------------".format(c5)
    print "{} Main Job Directory:          {}{}".format(c1,c0,mcf[ "JobStreams" ])
    print "{} Simulation basename:         {}{}".format(c1,c0,mcf[ "BaseDirNames" ])
    print "{} Sbatch start template:       {}{}.template".format(c1,c0,mcf[ "SbatchEquilibrateScript" ])
    print "{} Sbatch prouction template:   {}{}.template".format(c1,c0,mcf[ "SbatchProductionScript" ])
    print "{} Optimization script:         {}{}".format(c1,c0,mcf[ "EquilibrateConfScript" ])
    print "{} Production script:           {}{}".format(c1,c0,mcf[ "ProductionConfScript" ])
    print "{} Namd modulefile:             {}{}".format(c1,c0,mcf[ "ModuleFile" ])

#   # checking the list in master config file for all replicate folders and runs(more than one replicate and run can be declared):
    try:
        Replicates   = mcf[ "JobReplicates" ]
        Runs         = mcf[ "Runs" ]
        nReplicates  = int(len(Replicates))
        nRuns        = int(len(Runs))
    except:
        error = "Error reading master_config_file variables."
        sys.exit(error)
#   # calculating some numbers:
    for i in range(0, nReplicates):
        sr += int(Replicates[i])                        # total no. of job replicate
    for j in range(0, nRuns):
        run += int(Runs[j])                             # total no. of runs in each replicate
    spr = jd_prod[ "steps" ]                              # steps per run
    dcd = jd_prod[ "dcdfreq" ]                            # dcd write frequency
    dfs = int(jd_prod[ "natom" ])*12.0/(1024.0*1024.0)    # dcd frame size (based on number of atoms from psf)
    tdf = int(spr)/int(dcd)*int(run)*int(sr)            # total dcd frames 
    dfs = int(jd_prod[ "natom" ])*12.0/(1024.0*1024.0)    # dcd frame size (based on number of atoms from psf)
    tdf = int(spr)/int(dcd)*int(run)*int(sr)            # total dcd frames 
    tpd = tdf*dfs/(1024)                                # total production data 
    tst = (int(sr)*int(run)*int(jd_prod[ "timestep" ])*int(spr))/1000000.0  # total simulated time

    print "{}\nEstimation of data to be generated from the production run of this simulation:{}".format(c1,c0)
    print "{}--------------------------------------------------------------------------------".format(c1)
    print "{} Simulation directories:   {}%-8s      {}Runs per directory:   {}%s".format(c1,c0,c1,c0) % (sr,run)
    print "{} Steps per run:            {}%-8s      {}Dcdfreq in run:       {}%s".format(c1,c0,c1,c0) % (spr,dcd)
    print "{} Dcd frame size(MB)        {}%-8.3f    {}Total dcd frames:     {}%s".format(c1,c0,c1,c0) % (dfs,tdf)

    print " {}   Total simulated time:{}  %12.2f {}nanoseconds".format(c1,c0,cc1) %(tst)
    if not (tpd==0):
        print " {}   Total production data:{} %12.2f {}GB".format(c1,c0,c1) %(tpd) 
    else:
        print " {}   Total production data:{} %12.2f {}GB {} - error in calculating frame size. No psf file?".format(c1,c1,c1,c0) %(tpd) 
    print "{}\nNode configuration:{}".format(c1,c0)
    print "{}--------------------------------------------------------------------------------".format(c5)
    print "{}Sbatch Scripts:     {} %s , %s  ".format(c1,c0) % (mcf[ "SbatchEquilibrateScript" ], mcf[ "SbatchProductionScript" ])      
    print "{}nodes:              {} %-12s    ".format(c1,c0) % (mcf[ "nodes" ])
    print "{}walltime:           {} %-12s    ".format(c1,c0) % (mcf[ "Walltime" ])
    print "{}no. tasks per node: {} %-12s    ".format(c1,c0) % (mcf[ "ntpn" ]) 
    print "{}processes per node: {} %-12s    ".format(c1,c0) % (mcf[ "ppn" ])
    if not mcf[ "Account" ] == "VR0000":
        print "{}account:            {} %-12s    ".format(c1,c0) % (mcf[ "Account" ])
    else:
        print "{}account:            {} %-12s{}-have you set your account?{} ".format(c1,c1,c1,c0) % (mcf[ "Account" ])

    print "{}\nChecking configuration input files:{}".format(c1,c0)
    print "{}--------------------------------------------------------------------------------".format(c5)

#   # checking if files in configuration exist where they are supposed to be. 
    print "{}{}:{}".format(c5,mcf[ "EquilibrateConfScript" ],c0)
    check_file_exists(jd_opt[ "psffilepath" ])
    check_file_exists(jd_opt[ "pdbfilepath" ])
    for i in jd_opt_pl:
        check_file_exists(i)

    print "{}{}:{}".format(c5,mcf[ "ProductionConfScript" ],c0)
    check_file_exists(jd_prod[ "psffilepath" ])
    check_file_exists(jd_prod[ "pdbfilepath" ])
    for i in jd_prod_pl:
        check_file_exists(i)


def check_file_exists(target):
    mesg1 = "{} found {} -ok!{}".format(c6,c5,c0)
    mesg2 = "{} found {} -ok!{} -example file?{}".format(c1,c1,c1,c0)
    mesg3 = "{} not found.{} -Check config file.{}".format(c1,c1,c0) 

    ntarget = target[6:]        # strip off "../../"
    if not "../../" in target[0:6]:
        print "{}unexpected path structure to input files:{}".format(c1,c0)

    if os.path.exists(ntarget):
        if "example" in target:
            print "{} %-50s {}".format(cc1,mesg2) %(ntarget)    
        else:
            print "{} %-50s {}".format(cc1,mesg1) %(ntarget)
    else:
        print "{} %-46s {}".format(cc1,mesg3) %(ntarget)

def benchmark():
    """ -function to benchmark job """
# read job details:        
    mcf = read_master_config_file()
    jd_opt,  jd_opt_pl  = read_namd_job_details(mcf[ "EquilibrateConfScript" ])    
    print "{} Setting up jobs for benchmarking based on job config files.".format(c0)
# create temporary files/ figure out job size. 

# move files to /Setup_and_Config/Benchmarking / create dictionary/ json file.

# optimize job/ create sbatch_files. 

# start benchmarking jobs: 

# extract results 

# plot results. 


def get_current_dir_list(job_dir):
    """ Simple function to return a list of directories in a given path """
    file_list = []
    if os.path.isdir(job_dir):
       file_list =  os.listdir(job_dir)
    else:
        sys.stderr.write("No directories found in {}. Have you initialized?".format(job_dir))
 
    return file_list



def get_curr_job_list(job_dir):
    """<high-level description of the function here>

    Argument(s):
        job_dir -- path to the job directory.

    Notes:
        <notes of interest, e.g. bugs, caveats etc.>

    Returns:
        <description of the return value>

    """

    # are you after a list of jobs or a list of files?
    file_list = []

    if os.path.isdir(job_dir):
        # build a list of every file in the `job_dir` directory tree. 
        # you may want to ignore files such as '.gitkeep' etc.
        for root, _, fns in os.walk(job_dir):
            for fn in fns:
                file_path = os.path.join(root, fn)
                if os.path.isfile(file_path):
                    file_list.append(file_path)

        #
        # insert code to manipulate `file_list` here.
        #
        
        file_list.sort()
    else:
        # NOTE: to developers, it is good practise to write error messages to
        # `stderr` rather than to stdout (i.e. avoid using`print` to display
        # error messages).
        sys.stderr.write("{} doesn't exist, it needs to be initialised.{}"
                .format(job_dir, os.linesep))

    return file_list


def execute_function_in_job_tree( func, *args ):
    """ -a generic function to execute a given function throughout the entire job tree """
    cwd = os.getcwd()
#   # read job structure tree as given in the "master_config_file":
    try:
        JobStreams, Replicates, BaseDirNames, JobBaseNames, Runs, nJobStreams, nReplicates, nBaseNames = check_job_structure() 
    except: 
        sys.stderr.write("Trouble reading job structure from 'master_config_file' ")

    # descending into Job Tree
    for i in range(0,nJobStreams):
        CurrentJobStream = cwd + '/' + JobStreams[i]

        if os.path.isdir(CurrentJobStream):
        # descending into Job Directory Tree of each Jobstream         
            JobStreamDirList = get_current_dir_list(CurrentJobStream) 
            for j in JobStreamDirList:
                CurrentJobDir = CurrentJobStream + '/' + j
                if os.path.isdir(CurrentJobDir):
                    try:
                        os.chdir(CurrentJobDir)
                        func( *args) 
                    except:
                        print "\nCan't descend into job directory tree. Have you populated?\n {}".format(CurrentJobDir)     
        else: 
            print "Can't see job directories {}   -Have you initialized?".format(CurrentJobStream)  


def test_function( args ):
    """testing function"""
    print "hi there from "
    cwd2 = os.getcwd()
    print cwd2, args 
     

def start_all_jobs():
    """ function for starting all jobs """
    mcf = read_master_config_file()
    startscript = mcf[ "SbatchEquilibrateScript" ]
    execute_function_in_job_tree( start_jobs, startscript )

def start_jobs( startscript ):
    """ function to start jobs in a directory"""
    cwd = os.getcwd()
    job_status, jobid = check_if_job_running()
    if job_status == "Ready" and jobid == "0":
        try: 
            print startscript
            subprocess.Popen(['sbatch', startscript])
            status = "submitted"
            key    = "JobStatus"
            update_local_job_details( key, status )
            status = "submitted to job queue"
            key    = "JobMessage"
            update_local_job_details( key, status )
        except:
            sys.stderr.write("Trouble starting job.")     
    else:
        print "It appears a job already running here:{} : jobid:{}".format(cwd,job_status)

def clear_jobs():
    """ function for clearing all pausejob and stop flags """
    mcf = read_master_config_file()
    execute_function_in_job_tree( clear_all_jobs )

def clear_all_jobs():
    """ function to clear all stop flags in a directory"""
    cwd = os.getcwd()
    job_status, jobid = check_if_job_running()
    if job_status == "stopped":
        try: 
            status = "Ready"
            key    = "JobStatus"
            update_local_job_details( key, status )
            status = "0"
            key    = "CurrentJobId"
            update_local_job_details( key, status )
            status = "cleared stop flags"
            key    = "JobMessage"
            update_local_job_details( key, status )
            if  os.path.isfile( "pausejob" ):
                os.remove( "pausejob" )
            print "{} cleared stop flags in: {} {}".format( c2, cwd, c0 )
        except:
            sys.stderr.write("Trouble clearing stop flags.")     
    else:
        print "It appears a job is running here:{} : jobstatus:{}".format(cwd,job_status)


def restart_all_production_jobs():
    """ -function to restart_all_production_jobs """
    print "-- restarting production jobs."
    mcf = read_master_config_file()
    JobDir       = mcf[ "JobStreams" ]
    ProdCommand  = mcf[ "SbatchProductionScript" ]
    cwd = os.getcwd()
    jobdirlist = get_curr_job_list(JobDir)

    for i in jobdirlist:    
        # check current job status
        cjs = check_if_job_running(JobDir,i)
        if cjs == "running":
            print "Job already running in JobDir/{} ".format(i)
        else:
            path = JobDir + '/' + i 
            os.chdir(path)
            try:
                subprocess.Popen(['sbatch', ProdCommand])
            except:
                print "can't launch:  sbatch {} ".format(ProdCommand)
            os.chdir(cwd)


def recover_all_jobs():
    """ -function to recover and restore crashed jobs """
    print "-- recovering crashed jobs."


def stop_jobs():
    """ -function to stop all jobs, -either immediately or gently."""
    print "-- stopping all jobs"
    execute_function_in_job_tree(stop_all_jobs_immediately)

def stop_all_jobs_immediately():
    """ function to stop all jobs imediately"""
    job_status, jobid = check_if_job_running()
    if job_status == "stopped" or job_status == "Ready":
        try: 
            status = "tried to stop job: none appears running."
            key    = "JobMessage"
            update_local_job_details( key, status )
        except:
            print "trouble updating job details."     
    else:
        try:
            subprocess.Popen([ 'scancel', jobid ])
            print " stopping job: {}".format( jobid )
            status = "sent scancel command."
            key    = "JobMessage"
            update_local_job_details( key, status )
            status = "stopped"
            key    = "JobStatus"
            update_local_job_details( key, status )
        except:
            print "unable to cancel job"

def new_round():
    """ -function to set up a new round of simulations."""
    print "-- setting up new simulation round"

def erase_all_data():
    """ -function to erase all data for a clean start.  Use with caution!"""
    mcf = read_master_config_file()
    try:
        JobStreams, Replicates, BaseDirNames, JobBaseNames, Runs, nJobStreams, nReplicates, nBaseNames = check_job_structure()
    except:
        sys.stderr.write("Trouble reading job structure from 'master_config_file' ")

    cwd = os.getcwd()
    print "\nWe are about to erase all data in this directory, which can be useful" 
    print "for making a clean start, but disasterous if this is the wrong folder!"
    print "{}Proceed with caution!{}".format(c4,c0)
    print "This operation will delete all data in the folders:\n"
    print "{}/{}                              {}".format(c1,JobStreams,c0) 
    print "{}/JobLog/                         {}- Job logs.{}".format(c2,cc1,c0) 
    print "{}/Setup_and_Config/Benchmarking/  {}- Benchmarking data.{}".format(c2,cc1,c0) 

    print("\nPress 'enter' to quit or type: '{}erase all my data{}':").format(c4,c0)
    str = raw_input("")
    if str == "erase all my data": 
        print "Ok, well if you say so...."
        for j in range(0,nJobStreams):
            TargetDir = cwd + "/" + JobStreams[j] 
            print " Erasing all files in:{}".format(TargetDir)
        if os.path.isdir(TargetDir):
            shutil.rmtree(TargetDir)
        else:
            print " Couldn't see {}".format(TargetDir)
        print "\nOh the humanity. I sure hope that wasn't anything important."
    else: 
        print "Phew! Nothing erased."


def clone():
    """ -function to clone directory without data, but preserving input files."""
    print "-- cloning data directory!!" 




