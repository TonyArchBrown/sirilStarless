#!/usr/bin/env python
import subprocess
import sys
import os
import getopt
from datetime import datetime
from PIL import Image
from pysiril.siril import Siril
from pysiril.addons import Addons
from pysiril.wrapper import Wrapper
from astropy.io import fits

def set_defaults():
    global arg_sourcefile

    # Set default args
    arg_sourcefile = 1

def init(argv):
    arg_help = "{0} -s <Target File with Stars in Fits format> ".format(argv[0])
    
    # Set the defaults
    set_defaults()

    try:
        opts, args = getopt.getopt(argv[1:], "hs:", ["help", "sourcefile=" ])
        # Minimum number of arguments are bias location and target name - all others can de defaulted
        if len(opts)<1:
            print(arg_help)  # print the help message
            sys.exit(3)
    except:
        print(arg_help)
        sys.exit(2)
    
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(arg_help)  # print the help message
            sys.exit(2)
        elif opt in ("-s", "--sourcefile"):
            global arg_sourcefile
            arg_sourcefile = arg

# Run expect first argument to be the filename of the file to process
#  defaults are provided as _s for the starless image, and use a stride of 256
#  which is a recommended default from the author of starless++
#  Create_Tiffs makes sure that 16bit Tiff versions as well as the Fits are available
#  this is useful for PS processing
def Process():   

    # Local constants
    trailer = '_starless'
    stride='256'
    create_tiff=True

    # Initialise globals from passed in args
    init(sys.argv)

    # Preparing pysiril
    print('Starting PySiril')
    app = Siril()
    cmd = Wrapper(app)
    app.tr.Configure(False,False,True,True)
    
    # Turn on or off (True or False) the Siril verbose output
    app.MuteSiril(False)
    app.Open()
    print('*****************************************')
    print('Processing Started at ' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    print('*****************************************')
    print('  INPUTS: -')
    print('    Source file = ' + arg_sourcefile)
    print('*****************************************')
   
    #Get attributes ((path & name) and extension)) of the input file
    # based on the input file name and path define all the other files artefacts that will be created
    srcInput=arg_sourcefile
    srcFilename, srcExt=os.path.splitext(srcInput)
    srcFilenameAsTif = srcFilename + '.tif'
    fileroot, file_extension=os.path.splitext(srcFilenameAsTif)

 #   filename, inputfile_extension=os.path.splitext(arg_sourcefile)
    
    if srcExt!='.fits' and srcExt!='.fit': 
        print ('ABORTED: Source file is not a FIT/FITS file')
        app.Close()
        del app
        sys.exit(2)
    # Set the Fit extension
    cmd.setext('fit')

    # set the working directory to the current directory
    workdir = os.getcwd()
    cmd.cd(workdir)
    
    # Open the original input 32b FITS file
    # convert it into 16b and save as TIF file with the same name
    cmd.load(srcFilename)          
    cmd.set16bits
    cmd.savetif(srcFilename)

    #Define the 16b version of the initial file, used as input for Starnet++
    #filename_tif = filename + '.tif'   

    #Get attributes (name and extension) of the tif file
    fileroot, file_extension=os.path.splitext(srcFilenameAsTif)

    #Define the output file we want Starnet++ to output which will be:-
    #  original name + trailer + ".tif"
    outputfile_extension=".tif"
    outputfilename=srcFilename+trailer+outputfile_extension
    
    #No spaces must exists in the path or filename as input to starnet
    if ' ' in srcFilenameAsTif:
        print ('FAILURE: No space allowed in file name or file path')
        app.Close()
        del app
        sys.exit(10)

        
    # We now check to make sure the TIF written is a 16 bit RGB file
    # not sure why it would not be as we set out to write this format above but
    # this iw what the original script does!
    im = Image.open(srcFilenameAsTif)
    imode=im.mode
    im.close()
    
    ## Few results of "mode" method according to file format input
    ##          color   Mono
    ## fits 32     F       F
    ## fits 16     F       F
    ## fits 16u    F       F
    ## fits 8      F       F
    ## Tif 32      /       F
    ## Tif 16      RGB     I;16  (the only file format usable by Starnet)
    ## Tif 8       RGB     L

    # starnet will only deal with 16bit RGB or Mono images
    if ((imode=='I;16' or imode=='RGB') and file_extension=='.tif') :
        # Set up string that will kick off Starnet++, NOTE startnet++ expected to be in pwd
        args= "./starnet++ " + srcFilenameAsTif + " " + outputfilename + " " + stride
        print ('Starnet++ is running...')
        subprocess.call(args, shell=True)
    else: 
        print ('Not a TIF/16bit file')
        app.Close()
        del app
        sys.exit(10)

    # We should now have a starless tiff file, make a 32b fit from this 
    starless_filename = fileroot + trailer
    cmd.load(starless_filename)             # Load original+_starless.tif
    cmd.set32bits
    cmd.fmul('1.0')
    cmd.save(starless_filename)             # Save original+bla_starless.fits

    # Now create the Stars.fits file by subtracting starless from original fits
    folder,_ = os.path.split(starless_filename)
    stars=srcFilename+"_stars"
    cmd.load(arg_sourcefile)                # Load original, stars+neb
    cmd.isub(starless_filename)             # subtract starless version
    cmd.save(stars)                         # save stars.FITS

    # The following was in the original to remove the TIFF files.  
    # However, the Starless and star tiff versions I will keep to allow Photoshop processing
    # Deletion of TIF temp files  
    # tokill=starless_filename + '.tif'         
    # os.remove(tokill)                       #Remove bla_s.tif  
    # For a currently unknown reason this does not appear to be working in script but does work if manually performed.
    # srcFilename, inputfile_extension=os.path.splitext(stars)
    # cmd.load(stars)          
    # cmd.set16bits
    # cmd.savetif(srcFilename)
    print('!REMINDER!/n - the automated creation of the TIF version of the FIT Stars file does not work, /n if you want this please create manually using Siril Export of fit stars.')
    
    os.remove(srcFilenameAsTif)              # Remove original Input tif we created 

    print('*****************************************')
    print('Processing Completed at ' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    print('*****************************************')

    try:
        app.Close()
        del app
    except Exception as e:
        print('ERROR Terminating ' + str(e))

# Boiler plate to allow inclusion as package, other wise Run, passing the filename of the file to 
# process
if __name__ == "__main__":
    Process()