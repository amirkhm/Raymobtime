import sys
import os
import bpy
import csv
import src.modules.blensor as blensor
import numpy as np
from bpy import data as D
from mathutils import *
from math import *
from datetime import datetime
from src.scripts.helpers import format_run_name
from src.modules.blensor.utils import *

def simulator():
    """
    Run the Blensor LiDAR simulation over a range of Raymobtime runs.

    This function reads simulation paths and run limits from command-line
    arguments, iterates over the selected simulation runs, loads vehicle
    positions from the SUMO output file, updates the Blender scene with the
    corresponding vehicle models, and performs LiDAR scans for receiver
    vehicles.

    The function also removes temporary vehicle objects and Blensor scan data
    after each run, hides remaining animated objects at the end of the process,
    reports the total execution time, and closes Blender.

    Expected command-line arguments:
        --simulation: Path to the folder containing ray-tracing simulation runs.
        --veh_path: Path to the Blender vehicle model file or directory.
        --from_run: First run index to process.
        --to: Final run index limit. The loop processes runs in the interval
            [from_run, to).

    Raises:
        ValueError: If run indices cannot be converted to integers.
        FileNotFoundError: If a required simulation run folder or SUMO output
            file is missing.
        KeyError: If required command-line arguments are not provided.
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

def getInfoVehicles(sumo_info_file):
    """
    Read vehicle position information from a SUMO output CSV file.

    This function parses vehicle position, orientation, height, and receiver
    status from a SUMO-generated CSV file. The reported position is corrected
    from the vehicle front reference point to the approximate vehicle center
    used in the Blender scene. A height offset is added because fixed simulations
    may not store the final height value directly.

    Args:
        sumo_info_file: Path to the SUMO output CSV file containing vehicle
            information for a simulation scene.

    Returns:
        A dictionary indexed by vehicle ID. Each entry contains the adjusted
        InSite x and y coordinates, vehicle height, angle, receiver status,
        and z coordinate.

    Raises:
        FileNotFoundError: If the SUMO output file does not exist.
        ValueError: If numeric fields such as position, length, height, or angle
            cannot be converted to floats.
    """

    #first rotate and then translate
    with open(sumo_info_file) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='`')
        line = 0
        vPosition = {}
        for row in reader:
            isRx = False
            isTx = False
            if(row['receiverIndex'] != '-1'):
                isRx = True
            thisAngleInRad = np.radians(float(row['angle'])) #*np.pi/180
            deltaX = (float(row['length'])/2.0) * np.sin(thisAngleInRad)
            deltaY = (float(row['length'])/2.0) * np.cos(thisAngleInRad)
            #Added height because fixed simulation does not save the height value
            vPosition[row['veh']] = {'xinsite':str(float(row['xinsite']) - deltaX),'yinsite':str(float(row['yinsite']) - deltaY),'height':float(row[' height'])+4,'angle':row['angle'],'isRx':isRx, 'z3':row['z3']}

    return vPosition

def doScan(vPosition, pathdir):
    """
    Perform LiDAR scans for receiver vehicles in the Blender scene.

    This function iterates over the vehicle position dictionary and performs
    a Blensor LiDAR scan only for vehicles marked as receivers. For each receiver,
    the scanner is positioned above the vehicle, configured for a 360-degree scan,
    and the generated point cloud is saved as a PCD file. The scan directory is
    then compressed and removed.

    Args:
        vPosition: Dictionary containing vehicle position data and receiver
            status. Each entry must include adjusted x and y coordinates, height,
            receiver flag, and z coordinate.
        pathdir: Temporary directory where the generated scan files will be saved.

    Raises:
        KeyError: If required vehicle fields are missing.
        ValueError: If position or height values cannot be converted to floats.
        FileNotFoundError: If expected scan output files are missing during cleanup.
    """

    for camera in vPosition.items():
        if camera[1]['isRx']:
            os.mkdir(pathdir)
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
            os.remove(pathdir+'/'+camera[0])
            doZip(pathdir)
            myfile = pathdir+'/'+camera[0]
            '''doClean(myfile)'''


if __name__ == "__main__":
    simulator()
