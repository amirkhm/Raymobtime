import sys
import os
import bpy
import blensor
from bpy import data as D
from mathutils import *
from math import *
from datetime import datetime
from src.scripts.helpers import format_run_name
from src.modules.blensor.utils import *

def simulator():
    """
    Run the Blensor LiDAR simulation over a range of Raymobtime runs.

    This function reads the simulation directory, vehicle model path, and run
    interval from command-line arguments. For each selected run, it loads vehicle
    position data from the SUMO output file, updates the Blender scene with the
    corresponding vehicle objects, and performs LiDAR scans for receiver or
    transmitter vehicles.

    After each run, temporary vehicle objects and Blensor scan data are removed.
    At the end of the simulation, the remaining animated objects are hidden, the
    total execution time is printed, and Blender is closed.

    Expected command-line arguments:
        --simulation: Path to the directory containing ray-tracing simulation runs.
        --veh_path: Path to the Blender vehicle model file or directory.
        --from_run: First run index to process.
        --to: Final run index limit. Runs are processed in the interval
            [from_run, to).

    Raises:
        ValueError: If the run indices cannot be converted to integers.
        ValueError: If one of the expected command-line flags is missing.
        FileNotFoundError: If a required run folder or SUMO output file is missing.
    """

    startTime = datetime.now()
    # Get infos from the args
    args = sys.argv
    folder_scanned_name = args[args.index('--simulation')+1]
    vehicles_blend_path = args[args.index('--veh_path')+1]
    start_run = int(args[args.index('--from_run')+1])
    end_run = int(args[args.index('--to')+1])
    frame_num = 0
    frame_step = 1
    run = start_run
    bpy.data.scenes['Scene'].frame_end = end_run-1
    bpy.data.scenes['Scene'].frame_start = 0
    if bpy.data.objects.get("Camera") is None:
        bpy.context.scene.camera = bpy.data.objects['Camera']
    bpy.context.scene.camera = bpy.data.objects['Camera']
    while run<end_run:
        print('Processing run' + str(run) + ' ...') 
        time_elapsed = datetime.now() - startTime
        scene_path = os.path.join(folder_scanned_name,format_run_name(run)) 
        if not os.path.exists(scene_path):
            print('\nWarning: could not find file ', scene_path , ' Stopping...')
            break
        sumo_info_file = os.path.join(scene_path,'sumoOutputInfoFileName.txt')
        vPosition = getInfoVehicles(sumo_info_file)
        Position = vPosition
        animateVehiclesBlender(Position, vehicles_blend_path) 
        doScan(Position,'scans_'+format_run_name(run))
        for obj in D.objects:
            if obj.name.startswith('flow') or obj.name.startswith('_flow'):
                obj.select = True
                bpy.ops.object.delete()
        bpy.ops.blensor.delete_scans()
        run += 1
        frame_num += frame_step

    endAnimation(frame_num)
    time_elapsed = datetime.now() - startTime
    print("Total time elapsed: " + str(time_elapsed))
    bpy.ops.wm.quit_blender()

def doScan(vPosition, pathdir):
    """
    Perform LiDAR scans for receiver and transmitter vehicles in the Blender scene.

    This function iterates over the vehicle position dictionary and performs a
    Blensor LiDAR scan for each vehicle marked as a receiver or transmitter. For
    each selected vehicle, the corresponding car object is temporarily hidden,
    the scanner is placed above the vehicle, and a 360-degree point cloud scan is
    generated and saved as a PCD file. The output directory is then compressed
    and removed.

    Args:
        vPosition: Dictionary containing vehicle position data. Each entry must
            include adjusted x and y coordinates, height, receiver/transmitter
            flags, and vehicle identifier.
        pathdir: Temporary directory where the generated scan files will be saved.

    Raises:
        KeyError: If a required vehicle field is missing.
        ValueError: If position or height values cannot be converted to floats.
        FileNotFoundError: If an expected scan output file is missing during
            cleanup.
    """

    for camera in vPosition.items():
        if camera[1]['isRx'] or camera[1]['isTx']:
            os.mkdir(pathdir)
            car_to_hide = bpy.data.objects[camera[0]]
            car_to_hide.hide_render = True
            car_to_hide.keyframe_insert(data_path="hide_render", index=-1)
            height = float(camera[1]['height']) + 1; # one meter above the car
            scanner = bpy.data.objects["Camera"]
            scanner.location.xyz = float(camera[1]['xinsite']),float(camera[1]['yinsite']),height # X,Y,Z
            scanner.rotation_euler = (radians(90), radians(0), radians(0))
            pcd_file_name = os.path.join(pathdir, f'{camera[0]}.pcd')
            blensor.blendodyne.scan_advanced(scanner, rotation_speed = 10.0, 
                                simulation_fps=24, angle_resolution = 0.1728, 
                                max_distance = 120, evd_file= pcd_file_name,
                                noise_mu=0.0, noise_sigma=0.03, start_angle = 0.0, 
                                end_angle = 360.0, evd_last_scan=True, 
                                add_blender_mesh = False, 
                                add_noisy_blender_mesh = False, world_transformation=scanner.matrix_world)
            car_to_hide.hide_render = False
            os.remove(pathdir+'/'+camera[0])
            doZip(pathdir)
            myfile = pathdir+'/'+camera[0]
            '''doClean(myfile)'''

def doClean(myfile):
    """
    Remove a file if it exists.

    This helper function checks whether the specified file exists and deletes it.
    If the file is not found, an error message is printed instead of raising an
    exception.

    Args:
        myfile: Path to the file that should be removed.
    """
    
    if os.path.isfile(myfile):
        os.remove(myfile)
    else:    ## Show an error ##
        print("Error: %s file not found" % myfile)

if __name__ == "__main__":
    simulator()
