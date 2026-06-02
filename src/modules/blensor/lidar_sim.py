import os
import bpy
import src.modules.blensor as blensor
import shutil
from bpy import data as D
from mathutils import *
from math import *
from datetime import datetime
from src.modules.blensor.utils import *
from src.scripts.helpers import format_run_name

def simulator():
    """
    Run the Blensor LiDAR simulation for a single Raymobtime run.

    This function loads the runtime configuration passed by the Blensor launcher,
    retrieves the ray-tracing output directory, scan output directory, and vehicle
    model path, and then performs LiDAR scanning for the selected simulation run.

    For each run, the function reads vehicle positions from the SUMO output file,
    updates the Blender scene with the corresponding vehicles, performs scans for
    receiver or transmitter vehicles, removes temporary scene objects, clears
    Blensor scan data, and finally closes Blender.

    Raises:
        RuntimeError: If the runtime configuration arguments are missing or invalid.
        FileNotFoundError: If a required run folder or SUMO output file is missing.
        KeyError: If required configuration fields are missing from the runtime
            configuration dictionary.
    """

    startTime = datetime.now()
    # Get infos from the args
    run_id, cfg = load_runtime_config()

    folder_scanned_name = cfg["paths"]["rt_simulations_dir"]
    folder_scans_dataset = cfg["paths"]["scans_dir"]
    vehicles_blend_path = cfg["paths"]["vehicles_blend_path"]

    start_run = run_id
    end_run = run_id + 1

    if not os.path.exists(folder_scans_dataset):
        os.makedirs(folder_scans_dataset)
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
        doScan(Position,'scans_'+format_run_name(run), folder_scans_dataset)
        for obj in D.objects:
            if obj.name.startswith('flow') or obj.name.startswith('_flow'):
                obj.select = True
                bpy.ops.object.delete()
                bpy.data.objects.remove(obj, do_unlink=True)
        bpy.ops.blensor.delete_scans()
        run += 1
        frame_num += frame_step

    endAnimation(frame_num)
    cleanup_scene()
    time_elapsed = datetime.now() - startTime
    print("Total time elapsed: " + str(time_elapsed))
    bpy.ops.wm.quit_blender()

def cleanup_scene():
    """
    Remove Blender scene data and purge unused resources.

    This function deletes all objects from the current Blender scene, removes
    unused meshes, materials, and textures, forces Python garbage collection,
    and purges orphaned Blender data blocks. It is intended to reduce memory
    usage after a Blensor simulation run.

    Raises:
        RuntimeError: If Blender fails to remove or purge scene data.
    """

    # Unlink all objects
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    
    # Purge orphaned data blocks
    for block in [bpy.data.meshes, bpy.data.materials, bpy.data.textures]:
        for item in block:
            block.remove(item)
    
    # Force garbage collection
    gc.collect()
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

def doZip(pathdir, scans_output):
    """
    Compress a scan directory into a ZIP file and remove the original directory.

    The ZIP file is created inside the scan output directory, using the scan
    directory name as the archive name. After compression, the temporary scan
    directory is deleted to reduce disk usage.

    Args:
        pathdir: Temporary directory containing the generated scan files.
        scans_output: Directory where the ZIP archive should be saved.

    Raises:
        FileNotFoundError: If the scan directory does not exist.
    """

    zip_output = os.path.join(scans_output, pathdir)
    cmd = f"zip -r -j {zip_output}.zip {pathdir}"
    os.system(cmd)
    print(cmd)
    shutil.rmtree(pathdir)

def doScan(vPosition, pathdir, scans_output):
    """
    Perform LiDAR scans for receiver and transmitter vehicles.

    This function iterates over the vehicle position dictionary and performs a
    Blensor LiDAR scan for each vehicle marked as receiver or transmitter. For
    each selected vehicle, the scanner is placed above the vehicle, configured
    for a 360-degree scan, and used to generate a PCD point cloud. The scan
    directory is then compressed and removed.

    Args:
        vPosition: Dictionary containing vehicle position data. Each entry must
            include adjusted x and y coordinates, height, receiver/transmitter
            flags, and z coordinate.
        pathdir: Temporary directory where generated scan files will be stored.
        scans_output: Directory where the compressed scan output should be saved.

    Raises:
        KeyError: If required vehicle fields are missing.
        ValueError: If position or height values cannot be converted to floats.
        FileNotFoundError: If expected scan files are missing during cleanup.
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
            doZip(pathdir, scans_output)
            myfile = pathdir+'/'+camera[0]
            '''doClean(myfile)'''

if __name__ == "__main__":
    simulator()
