import os
import csv
import shutil
import numpy as np
from bpy import data as D
from bpy import context as C
from mathutils import *
from math import *
from datetime import datetime
from zipfile import ZipFile
from src.scripts.helpers import format_run_name
from src.modules.blensor.utils import *

def main():

    """
    Run the Base Station image simulation for a single Raymobtime run.

    This function loads the runtime configuration passed by the Blensor launcher,
    retrieves the paths required for ray-tracing results, image output, and vehicle
    Blender models, and renders images from the configured Base Station cameras.

    The function processes only one run per execution. The run identifier is
    received from the runtime configuration arguments, and the function searches
    for the corresponding ray-tracing output folder. Vehicle positions are read
    from the SUMO output file, animated in the Blender scene, and then images are
    rendered for each configured camera.

    Raises:
        RuntimeError: If the runtime configuration arguments are missing or invalid.
        FileNotFoundError: If required input files such as the SUMO output file are
            missing during processing.
        NameError: If a configured camera object is not found in the Blender scene.
    """

    startTime = datetime.now()

    run_id, cfg = load_runtime_config()

    folder_scanned_name = cfg["paths"]["rt_simulations_dir"]
    folder_img_dataset = cfg["paths"]["images_dir"]
    vehicles_blend_path = cfg["paths"]["vehicles_blend_path"]

    start_run = run_id
    end_run = run_id + 1

    if not os.path.exists(folder_img_dataset):
        os.makedirs(folder_img_dataset)

    useRays = False
    usePed = False

    c = 0
    frame_num = 0
    frame_step = 1
    run = start_run
    camera_n = cfg["blensor"]["n_camera_BS"]
    cameras = []
    for i in range(camera_n):
        cameras.append(f'Camera{i}')

    bpy.data.scenes['Scene'].frame_start = 0
    while run<end_run:
        print('Processing run' + str(run) + ' ...')
        time_elapsed = datetime.now() - startTime
        scene_path = os.path.join(folder_scanned_name,format_run_name(run))
        if not os.path.exists(scene_path):
            print('\nWarning: could not find file ', scene_path , ' Stopping...')
            break
        sumo_info_file = os.path.join(scene_path,'sumoOutputInfoFileName.txt')
        if usePed:
            sumo_ped_info_file = os.path.join(scene_path,'sumoOutputInfoFileNamePed.txt')

        path_info_file = os.path.join(scene_path,'study/model.paths.t001_01.r002.p2m')
        vPosition = getInfoVehicles(sumo_info_file)
        if usePed:
            vPedPosition = getInfoPedestrian(sumo_ped_info_file)
            Position = dict(vPosition, **vPedPosition)
        else:
            Position = vPosition
        animateVehiclesBlender(Position, vehicles_blend_path)
        for cam in cameras:
            take_image(cam, folder_img_dataset, run)
        for obj in D.objects:
            if obj.name.startswith('flow') or obj.name.startswith('_flow'):
                obj.select = True
                bpy.ops.object.delete()
        run += 1
        frame_num += frame_step

    endAnimation(frame_num)
    time_elapsed = datetime.now() - startTime
    print("Total time elapsed: " + str(time_elapsed))

def take_image(camera, output_folder_name, run):
    
    """
    Render and save an image from a specified Blender camera.

    This function selects a camera object from the current Blender scene,
    sets it as the active scene camera, defines the output file path, and
    renders a still image. The image is saved under the Base Station image
    output directory for the corresponding simulation run.

    Args:
        camera: Name of the Blender camera object to be used for rendering.
        output_folder_name: Base directory where rendered images will be saved.
        run: Simulation run identifier used to organize the output path.

    Raises:
        NameError: If the specified camera object is not found in the Blender scene.
    """

    scene = C.scene
    try:
        cam = D.objects[camera]
    except:
        raise NameError(f"\n\nERROR: object camera '{camera}' not found, try following the naming pattern CameraN in blender scenario")
    scene.camera = cam
    scene.render.filepath = os.path.join(output_folder_name, 'BS', f'run{run}', f'{camera}')
    bpy.ops.render.render(write_still = True)

def getInfoVehicles(sumo_info_file):
    
    """
    Read vehicle position information from a SUMO output CSV file.

    This function parses vehicle position, orientation, dimensions, and receiver
    status from a SUMO-generated CSV file. The vehicle position is adjusted from
    the reported front-bumper reference point to the approximate vehicle center
    used in the Blender/InSite coordinate system.

    Args:
        sumo_info_file: Path to the SUMO output CSV file containing vehicle
            information for a simulation scene.

    Returns:
        A dictionary indexed by vehicle ID. Each entry contains the adjusted
        InSite x and y coordinates, vehicle height, angle, receiver status,
        and z coordinate.
    """

    #first rotate and then translate
    with open(sumo_info_file) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='`')
        line = 0
        vPosition = {}
        for row in reader:
            row['isRx'] = False
            if(row['receiverIndex'] != '-1'):
                row['isRx'] = True
            thisAngleInRad = np.radians(float(row['angle'])) #*np.pi/180
            deltaX = (float(row['length'])/2.0) * np.sin(thisAngleInRad)
            deltaY = (float(row['length'])/2.0) * np.cos(thisAngleInRad)
            vPosition[row['object_id']] = {'xinsite':str(float(row['xinsite']) - deltaX),
                                     'yinsite':str(float(row['yinsite']) - deltaY),
                                     'height':row['height'],'angle':row['angle'],
                                     'isRx':row['isRx'], 'z3':row['z3']}

    return vPosition

def getInfoPedestrian(info_file):
    """
    Read pedestrian position information from a SUMO output CSV file.

    This function parses pedestrian position, orientation, and receiver status
    from a SUMO-generated CSV file. The pedestrian position is adjusted using
    the same front-reference correction applied to vehicles and is formatted
    for use in Blender scene animation.

    Args:
        info_file: Path to the SUMO output CSV file containing pedestrian
            information for a simulation scene.

    Returns:
        A dictionary indexed by pedestrian ID with the prefix ``ped``. Each
        entry contains the adjusted InSite x and y coordinates, height, angle,
        receiver status, and z coordinate.
    """
    #first rotate and then translate
    with open(info_file) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='`')
        line = 0
        vPosition = {}
        for row in reader:
            row['isRx'] = False
            if(row['receiverIndex'] != '-1'):
                row['isRx'] = True
            thisAngleInRad = np.radians(float(row['angle'])) #*np.pi/180
            deltaX = (float(row['length'])/2.0) * np.sin(thisAngleInRad)
            deltaY = (float(row['length'])/2.0) * np.cos(thisAngleInRad)
            vPosition['ped'+row['ped']] = {'xinsite':str(float(row['xinsite']) - deltaX),'yinsite':str(float(row['yinsite']) - deltaY),'height':str(1.72),'angle':row['angle'],'isRx':row['isRx'], 'z3':0}

    return vPosition

def createLineBlender(objname, cList, frame_num, frame_step):
    """
    Create a 3D polyline object in Blender to represent a ray path.

    This function creates a curve object from a list of 3D points and assigns
    a material color according to the received power or path gain value
    associated with the ray. The generated object is hidden in previous frames
    and shown at the specified frame to support ray animation.

    Args:
        objname: Name assigned to the Blender curve object.
        cList: List of ray path points. Each point is expected to contain
            x, y, z coordinates and a received power or path gain value.
        frame_num: Frame in which the ray object should become visible.
        frame_step: Step used to define previous frames where the object
            should remain hidden.
    """

    curvedata = bpy.data.curves.new(name='curve', type='CURVE')
    curvedata.dimensions = '3D'

    objectdata = bpy.data.objects.new(objname, curvedata)
    objectdata.location = (0,0,0) #object origin
    bpy.context.scene.objects.link(objectdata)

    polyline = curvedata.splines.new('POLY')
    polyline.points.add(len(cList)-1)
    w = 100

    # Colors
    mat_red = bpy.data.materials.new("PKHG")
    mat_red.diffuse_color = (1,0,0)
    mat_blue = bpy.data.materials.new("PKHG")
    mat_blue.diffuse_color = (0,0,1)
    mat_green = bpy.data.materials.new("PKHG")
    mat_green.diffuse_color = (0,1,0)
    mat_orange = bpy.data.materials.new("PKHG")
    mat_orange.diffuse_color = (0.8,0.2,0)
    mat_yellow = bpy.data.materials.new("PKHG")
    mat_yellow.diffuse_color = (0.8,0.65,0)
    objectdata.data.materials.append(mat_red)
    for num in range(len(cList)):
        x, y, z, db = cList[num]
        polyline.points[num].co = (x, y, z, w)

    #classify by colors
    if ( db < -220 and db < -193):
        matchoose = mat_blue
    elif ( db < -166):
        matchoose = mat_green
    elif ( db < -151):
        matchoose = mat_yellow
    elif ( db < -138):
        matchoose = mat_orange
    else:
        matchoose = mat_red

    objectdata.active_material = matchoose
    objectdata.data.extrude = 0.1
    objectdata.data.bevel_depth = 0.1

    for i in range(0,frame_num,frame_step):
        bpy.context.scene.frame_set(i)
        objectdata.hide = True
        objectdata.hide_render = True
        objectdata.keyframe_insert(data_path="hide_render", index=-1)
        objectdata.keyframe_insert(data_path="hide", index=-1)

    bpy.context.scene.frame_set(frame_num)
    objectdata.hide = False
    objectdata.keyframe_insert(data_path="hide", index=-1)

def rayAnimation(vectorsPath,frame_num, frame_step):
    """
    Create Blender ray animations from a collection of propagation paths.

    This function iterates over a dictionary of ray paths and creates one
    Blender curve object for each ray using ``createLineBlender``.

    Args:
        vectorsPath: Dictionary containing ray path data indexed by ray ID.
        frame_num: Frame in which the generated ray objects should be shown.
        frame_step: Frame step used to hide the ray objects in previous frames.
    """

    for rays in vectorsPath.items():
        objname = str(frame_num)+'Ray'+str('%05d' % rays[0])
        createLineBlender(objname,rays[1], frame_num, frame_step)

def endRayAnimation(frame_num, frame_step):
    """
    Hide ray objects after their animation frame.

    This function advances the Blender scene to the frame immediately after
    the ray animation frame and hides all ray objects associated with the
    given frame number.

    Args:
        frame_num: Frame number associated with the ray objects to hide.
        frame_step: Frame step used to determine the next frame.
    """

    bpy.context.scene.frame_set(frame_num + frame_step)
    for x in range(0, len(bpy.context.scene.objects)):
        obj_name = bpy.context.scene.objects[x].name
        if obj_name.startswith(str(frame_num)): # Add to list
            bpy.data.objects[obj_name].hide_render = True
            bpy.data.objects[obj_name].hide = True
            bpy.data.objects[obj_name].keyframe_insert(data_path="hide_render", index=-1)
            bpy.data.objects[obj_name].keyframe_insert(data_path="hide", index=-1)

def endAnimation(frame_num):
    """
    Hide animated vehicle objects at the end of the animation.

    This function sets the Blender scene to the specified frame and hides all
    objects whose names start with ``flow``. Visibility keyframes are inserted
    to mark the end state of the animation.

    Args:
        frame_num: Frame number where the final visibility state should be set.
    """

    bpy.context.scene.frame_set(0)
    for x in range(0, len(bpy.context.scene.objects)):
        obj_name = bpy.context.scene.objects[x].name
        if obj_name.startswith('flow'): # Add to list
            bpy.data.objects[obj_name].hide_render = True
            bpy.data.objects[obj_name].hide = True
            bpy.data.objects[obj_name].keyframe_insert(data_path="hide_render", index=-1)
            bpy.data.objects[obj_name].keyframe_insert(data_path="hide", index=-1)

# if the vehicle does not exist, create it. if it exists, move it. if it existed and does not exist anymore, remove it.

def animateVehiclesBlender(vPosition, vehicles_blend_path):
    """
    Add, update, and animate vehicles in the Blender scene.

    This function synchronizes the Blender scene with the vehicle positions
    provided in ``vPosition``. Existing vehicles are moved and rotated according
    to the current scene data, missing vehicles are imported from a vehicle
    Blender file, and vehicles no longer present in the scene are hidden.

    Args:
        vPosition: Dictionary containing vehicle or pedestrian position data.
            Each entry must include adjusted x and y coordinates, height,
            angle, and z coordinate.
        vehicles_blend_path: Path to the Blender file or directory containing
            vehicle models to be appended to the scene.
    """

    bpy.context.scene.frame_set(0)

    # PRE-PROCESSING all vehicles that are in the scene 
    objects_in_scene = []
    for x in range(0, len(bpy.context.scene.objects)):
        obj_name = bpy.context.scene.objects[x].name
        if obj_name.startswith('flow') or obj_name.startswith('dflow') or obj_name.startswith('ped'): # Add to list

            if not obj_name in vPosition:
                bpy.data.objects[obj_name].hide_render = True
                bpy.data.objects[obj_name].hide = True
                bpy.data.objects[obj_name].keyframe_insert(data_path="hide_render", index=-1)
                bpy.data.objects[obj_name].keyframe_insert(data_path="hide", index=-1)
                bpy.data.objects[obj_name].name = '_'+bpy.data.objects[obj_name].name

    for vehicles in vPosition.items():
        if bpy.data.objects.get(vehicles[0]) is not None: # Existe, code to move

            veh = bpy.data.objects[vehicles[0]]
        else:
            if (float(vehicles[1]['height']) == 1.59): # Car
                bpy.ops.wm.append(directory=vehicles_blend_path.replace('/','//') + "/Object/", filepath="vehicles.blend", filename="Car")
                veh = bpy.data.objects["Car"]
            elif (float(vehicles[1]['height']) == 3.2): # Bus
                bpy.ops.wm.append(directory=vehicles_blend_path.replace('/','//') + "/Object/", filepath="vehicles.blend", filename="Bus")
                veh = bpy.data.objects["Bus"]
            elif (float(vehicles[1]['height']) == 4.3): # Truck
                bpy.ops.wm.append(directory= vehicles_blend_path.replace('/','//') + "/Object/", filepath="vehicles.blend", filename="Truck")
                veh = bpy.data.objects["Truck"]
            elif (float(vehicles[1]['height']) == 0.295): # Drone
                bpy.ops.wm.append(directory= vehicles_blend_path.replace('/','//') + "/Object/", filepath="vehicles.blend", filename="Drone")
                veh = bpy.data.objects["Drone"]
            else:
                continue

            veh.name = vehicles[0]

        veh.hide = False
        veh.hide_render = False
        ax,ay,az = veh.rotation_euler
        angle_to_rotate = 90-float(vehicles[1]['angle'])
        angle_to_rotate = chooseAngleToRotate(degrees(az),angle_to_rotate)
        veh.rotation_euler = (radians(0), radians(0), radians(angle_to_rotate))
        veh.location.xyz = float(vehicles[1]['xinsite']),float(vehicles[1]['yinsite']),float(vehicles[1]['z3'])#float(vehicles[1]['height'])/2 # X,Y,Z
        veh.keyframe_insert(data_path="hide_render", index=-1)
        veh.keyframe_insert(data_path="hide", index=-1)
        veh.keyframe_insert(data_path="location", index=-1)
        veh.keyframe_insert(data_path="rotation_euler", index=-1)


def buildVehiclesBlender(vPosition):
    """
    Build vehicle objects in Blender using predefined vehicle models.

    This function appends vehicle models from a Blender file according to the
    height of each vehicle and places them at the corresponding InSite
    coordinates.

    Args:
        vPosition: Dictionary containing vehicle position and dimension data.
            The vehicle height is used to select the appropriate model.
    """

    for vehicles in vPosition.items():
        if (float(vehicles[1]['height']) == 1.59): # Car
            bpy.ops.wm.append(directory=os.getcwd().replace('/','//') + "//vehicles.blend/Object/", filepath="vehicles.blend", filename="Car")
            veh = bpy.data.objects["Car"]
        elif (float(vehicles[1]['height']) == 3.2): # Bus
            bpy.ops.wm.append(directory=os.getcwd().replace('/','//') + "//vehicles.blend/Object/", filepath="vehicles.blend", filename="Bus")
            veh = bpy.data.objects["Bus"]
        elif (float(vehicles[1]['height']) == 4.3): # Truck
            bpy.ops.wm.append(directory= os.getcwd().replace('/','//') + "//vehicles.blend/Object/", filepath="vehicles.blend", filename="Truck")
            veh = bpy.data.objects["Truck"]
        veh.name = vehicles[0]
        veh.rotation_euler = (radians(0), radians(0), radians(90-float(vehicles[1]['angle'])))
        veh.location.xyz = float(vehicles[1]['xinsite']),float(vehicles[1]['yinsite']),0

def buildVehiclesBlenderBox(vPosition):
    """
    Build simplified box-shaped vehicle objects in Blender.

    This function creates cube primitives to represent vehicles and scales
    them according to predefined dimensions for cars, buses, and trucks.
    The boxes are positioned and rotated using the provided vehicle data.

    Args:
        vPosition: Dictionary containing vehicle position, height, and angle
            information.
    """

    for vehicles in vPosition.items():
        bpy.ops.mesh.primitive_cube_add(radius=1, location = (0,0,0)) # location X, Y, Z/2(center of cube is in its centroid)
        cube = bpy.data.objects["Cube"]
        cube.name = vehicles[0]
        if (float(vehicles[1]['height']) == 1.59): # Car
            cube.dimensions.xyz = 1.775,4.645,1.59
        elif (float(vehicles[1]['height']) == 3.2): # Bus
            cube.dimensions.xyz = 2.4,9,3.2
        elif (float(vehicles[1]['height']) == 4.3): # Truck
            cube.dimensions.xyz = 2.5,12.5,4.3
        cube.rotation_euler = (radians(0), radians(0), radians(180-float(vehicles[1]['angle'])))
        cube.location.xyz = float(vehicles[1]['xinsite']),float(vehicles[1]['yinsite']),float(vehicles[1]['height'])/2 # X,Y,Z

def doZip(pathdir):
    """
    Compress a directory into a ZIP file and remove the original directory.

    Args:
        pathdir: Path to the directory that should be compressed.
    """

    os.system('zip %s.zip -r -j %s'%(pathdir, pathdir))
    print('zip %s.zip -r -j %s'%(pathdir, pathdir))
    shutil.rmtree(pathdir)

def doScan(vPosition,pathdir):
    """
    Perform LiDAR scans for receiver vehicles in the Blender scene.

    This function places the Blensor scanner above each receiver vehicle,
    performs a 360-degree LiDAR scan, saves the generated point cloud, and
    compresses the output directory.

    Args:
        vPosition: Dictionary containing vehicle position and receiver status.
        pathdir: Directory where the scan files should be temporarily stored.
    """

    for camera in vPosition.items():
        if camera[1]['isRx']:
            os.mkdir(pathdir)
            car_to_hide = bpy.data.objects[camera[0]]
            car_to_hide.hide_render = True
            height = float(camera[1]['height']) + 1; # one meter above the car
            scanner = bpy.data.objects["Camera"]
            scanner.location.xyz = float(camera[1]['xinsite']),float(camera[1]['yinsite']),height # X,Y,Z
            scanner.rotation_euler = (radians(90), radians(0), radians(0))
            blensor.blendodyne.scan_advanced(scanner, rotation_speed = 10.0,simulation_fps=24, 
                                            angle_resolution = 0.1728, max_distance = 120,
                                            evd_file= pathdir+'/'+camera[0]+".pcd",noise_mu=0.0, 
                                            noise_sigma=0.03, start_angle = 0.0, end_angle = 360.0, 
                                            evd_last_scan=True, add_blender_mesh = False,
                                            add_noisy_blender_mesh = False, world_transformation=scanner.matrix_world)
            car_to_hide.hide_render = False
            print(pathdir+'/'+camera[0]+".pcd")
            doZip(pathdir)
            myfile = pathdir+'/'+camera[0]
            '''doClean(myfile)'''
    doZip(pathdir)

def doZipPython(filepath):
    """
    Compress a directory into a ZIP file using Python's zipfile module.

    This function recursively adds all files from the given directory to a ZIP
    archive and removes the original directory after compression.

    Args:
        filepath: Path to the directory that should be compressed.
    """

    with ZipFile(filepath+'Zipped.zip', 'w') as zipped:
        for folderName, subfolders, filenames in os.walk(filepath):
            for filename in filenames:
                filePath = os.path.join(folderName, filename)
                zipped.write(filePath)
                print('Write '+filePath)
    shutil.rmtree(filepath)

def doClean(myfile):
    """
    Remove a file if it exists.

    Args:
        myfile: Path to the file that should be deleted.
    """

    if os.path.isfile(myfile):
        os.remove(myfile)
    else:   
        print("Error: %s file not found" % myfile)

if __name__ == '__main__':
    main()
