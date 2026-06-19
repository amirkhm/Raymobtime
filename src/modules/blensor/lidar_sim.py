import os
import bpy
import blensor
import shutil
from bpy import data as D
from mathutils import *
from math import *
import gc
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
    Remove Blender scene data and unused resources.

    This function deletes all objects from the current Blender scene and
    removes unused data blocks without relying on context-dependent Blender
    operators. It is compatible with Blender/Blensor 2.79.
    """

    # Remove all objects safely.
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    # Remove unused meshes.
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)

    # Remove unused materials.
    for material in list(bpy.data.materials):
        if material.users == 0:
            bpy.data.materials.remove(material)

    # Remove unused textures.
    for texture in list(bpy.data.textures):
        if texture.users == 0:
            bpy.data.textures.remove(texture)

    # Remove unused images.
    for image in list(bpy.data.images):
        if image.users == 0:
            bpy.data.images.remove(image)

    # Remove unused curves.
    for curve in list(bpy.data.curves):
        if curve.users == 0:
            bpy.data.curves.remove(curve)

    # Remove unused cameras.
    for camera in list(bpy.data.cameras):
        if camera.users == 0:
            bpy.data.cameras.remove(camera)
    # Remove unused light
    for lamp in list(bpy.data.lamps):
        if lamp.users == 0:
            bpy.data.lamps.remove(lamp)

    gc.collect()

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

    Temporary scan files are generated inside the LiDAR output directory.
    For each receiver or transmitter, the scanner is positioned above the
    corresponding object and performs a 360-degree LiDAR scan. The generated
    temporary directory is then compressed into the LiDAR output directory.

    Args:
        vPosition: Dictionary containing vehicle position data. Each entry must
            include adjusted x and y coordinates, height, receiver/transmitter
            flags, and z coordinate.
        pathdir: Name or original path of the temporary scan directory. Only its
            final directory name is used, and the directory is created inside
            ``scans_output``.
        scans_output: Directory where LiDAR outputs and temporary scan files are
            generated.

    Raises:
        KeyError: If required vehicle fields are missing.
        ValueError: If position or height values cannot be converted to floats.
    """

    # Ensure that the LiDAR output directory exists.
    os.makedirs(scans_output, exist_ok=True)

    # Keep only the final directory name so that the temporary directory is
    # always created inside scans_output.
    temp_dir_name = os.path.basename(os.path.normpath(pathdir))

    if not temp_dir_name:
        temp_dir_name = "temp_scans"

    pathdir = os.path.join(scans_output, temp_dir_name)
    os.makedirs(pathdir, exist_ok=True)

    for vehicle_id, vehicle_data in vPosition.items():
        if not (vehicle_data["isRx"] or vehicle_data["isTx"]):
            continue

        car_to_hide = bpy.data.objects[vehicle_id]
        car_to_hide.hide_render = True
        car_to_hide.keyframe_insert(
            data_path="hide_render",
            index=-1
        )

        try:
            # One meter above the vehicle.
            vehicle_z = float(vehicle_data.get("z", 0.0))
            vehicle_height = float(vehicle_data["height"])
            scanner_height = vehicle_z + vehicle_height + 1.0

            scanner = bpy.data.objects["Camera"]

            scanner.location.xyz = (
                float(vehicle_data["xinsite"]),
                float(vehicle_data["yinsite"]),
                scanner_height
            )

            scanner.rotation_euler = (
                radians(90),
                radians(0),
                radians(0)
            )

            pcd_file_name = os.path.join(
                pathdir,
                "{}.pcd".format(vehicle_id)
            )

            blensor.blendodyne.scan_advanced(
                scanner,
                rotation_speed=10.0,
                simulation_fps=24,
                angle_resolution=0.1728,
                max_distance=120,
                evd_file=pcd_file_name,
                noise_mu=0.0,
                noise_sigma=0.03,
                start_angle=0.0,
                end_angle=360.0,
                evd_last_scan=True,
                add_blender_mesh=False,
                add_noisy_blender_mesh=False,
                world_transformation=scanner.matrix_world
            )

            generated_file = os.path.join(pathdir, vehicle_id)

            if os.path.exists(generated_file):
                os.remove(generated_file)

            doZip(pathdir, scans_output)

            myfile = os.path.join(pathdir, vehicle_id)
            # doClean(myfile)

        finally:
            # Ensure that the vehicle becomes visible again even when the scan
            # fails.
            car_to_hide.hide_render = False
            car_to_hide.keyframe_insert(
                data_path="hide_render",
                index=-1
            )

if __name__ == "__main__":
    simulator()
