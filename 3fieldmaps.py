import yt,os,sys,time,traceback,threading,glob
from yt import YTQuantity
from yt.units import dimensions
from setup import *
import multiprocessing as mp

# This is an interactive UI for loading in data sets to yt and performing SlicePlots.
# It takes raw_inputs from the user to determine the file(s), field, and axis to
# run the SlicePlots on. These inputs are written to a configuration file so it
# can be accessed by multiple processors when run in parallel. Every file is
# checked to make sure that the field and axes are valid inputs by the debug()
# function. Tags such as 'CONFIG OPEN', 'debug', and 'COMPLETE (2.2)' are
# printed to update the user on what is happening in the program.

# set resolution level of png (dpi)
quick = 150
pro = 1250
dpi_level = quick

################################################################################
def runfile((file_name,field,axis)):
    # runs a single file
    print "runfile"
    loadfile = yt.load(file_name)
    narf = ((loadfile.domain_right_edge-loadfile.domain_left_edge)/2.0)+loadfile.domain_left_edge
    slc = yt.SlicePlot(loadfile,axis,[field],origin = "native",center = [0,0,narf[2]],fontsize=14)
    rescale(slc,field)
    slc.annotate_timestamp(time_format="t = {time:.0f} {units}",draw_inset_box=True,corner='upper_left')
    # You can customize your slices here (ex. add contours,etc.)
    #slc.annotate_streamlines('velocity_z','velocity_x')
    slc.save(mpl_kwargs = {"dpi":dpi_level})
    return
def debug(file_name,field,axis):
    #checks for given fields in stored yt field lists
    print "debug"
    loadfile = yt.load(file_name)
    fields = [x[1] for x in loadfile.field_list] + [x[1] for x in loadfile.derived_field_list]
    if field in fields:
        axes = ["x","y","z"]
        if axis not in axes:
            print "ERROR: invalid axis ({0})".format(axis)
            return False
        return True
    else:
        print "ERROR: field not available ({0})".format(field)
        return False
def rescale(plot,field):
    if field == "met_O":
        # resizes axis of metallicity plot to limits defined in Gritton et al, 2014
        plot.set_zlim("met_O",0.0001,1.0)
    if field == "velocity_Z":
        plot.set_log("velocity_Z",False)
    if field == "mach_speed":
        plot.set_log("mach_speed",False)
    if field == "velocity_z":
        plot.set_zlim("velocity_z",-1.5e7,1.5e7)
        plot.set_log("velocity_z",False)
    if field == "ram_pressure":
        plot.set_zlim("ram_pressure",3e-17,1e-12)
    #if field == "density":
    #    plot.set_zlim("density",1e-27,1e-22)
    return plot
def save_data(field,axis,fl_list):
    # saves sliceplots to separate directory inside working directory
    directory = os.getcwd() + "/{1}_{0}".format(axis,field)
    if not os.path.exists(directory):
        os.makedirs(directory)
    for fl_nm in fl_list:
        source_file = os.getcwd() + "/{0}_Slice_{1}_{2}.png".format(fl_nm,axis,field)
        destination = os.getcwd() + "/{2}_{1}/{0}_Slice_{1}_{2}.png".format(fl_nm,axis,field)
        if os.path.exists(source_file):
            print "moving {}...".format(source_file)
            os.rename(source_file, destination)
    print "Data saved to: {2}/{1}_{0}".format(axis,field,os.getcwd())
################################################################################
# Running the program

# input function is run serially to only write parameters to config file once
if __name__ == '__main__':
    full = raw_input("run all files? (y/n): ")
    fl_nm = raw_input("enter filename: ").strip()
    field = raw_input("field to run: ")
    axis = raw_input("axis(if y hit return): ")
    if axis == "":
        axis = "y"
    if full != "y":
        full = "n"

    if full == "y":
        file_list = glob.glob(fl_nm[0:-4] + "*")
        if debug(fl_nm,field,axis) == False:
            sys.exit()
    else:
        file_list = [fl_nm]

    arg_list = zip(file_list,[field]*len(file_list),[axis]*len(file_list))

    cpu_cores = mp.cpu_count()
    pool = mp.Pool(processes=(cpu_cores-1))
    t0 = float(time.time())
    pool.map(runfile,arg_list)
    pool.close()
    pool.join()
    if full == "y":
        save_data(field,axis,file_list)
    t1 = float(time.time())
    print "FIELD: " + field
    print "AXIS: " + axis
    print timer(t1 - t0)
