import os
import bpy
import csv
import numpy as np
from bpy import data as D
from bpy import context as C
from mathutils import *
from math import *
from datetime import datetime
from src.scripts.helpers import format_run_name
from src.modules.blensor.utils import *

def main():
    """
    Run the User Equipment image simulation for a single Raymobtime run.

    This function loads the runtime configuration passed by the Blensor launcher,
    retrieves the required ray-tracing output paths, image output paths, vehicle
    model path, and scene metadata, then renders images from the perspective of
    receiver vehicles.

    The function processes one simulation run per execution. It reads vehicle
    positions from the SUMO output file, loads ray-tracing path information,
    updates the vehicle objects in the Blender scene, and captures multiple
    images around each valid receiver vehicle using ``get4Photos``.

    The current episode and scene counters are updated according to the number
    of scenes per episode provided in the runtime configuration.

    Raises:
        RuntimeError: If the runtime configuration arguments are missing or
            invalid.
        FileNotFoundError: If required input files, such as the SUMO output file,
            ray-tracing path file, or CoordVehicleTxRx CSV file, are missing.
    """

    startTime = datetime.now()
    frame_num = 0

    run_id, cfg = load_runtime_config()

    folder_scanned_name = cfg["paths"]["rt_simulations_dir"]
    folder_img_dataset = cfg["paths"]["images_dir"]
    vehicles_blend_path = cfg["paths"]["vehicles_blend_path"]

    start_run = run_id
    end_run = run_id + 1
    n_scenes_of_each_episode = cfg["simulation"]["scenes_per_episode"]

    if not os.path.exists(folder_img_dataset):
        os.makedirs(folder_img_dataset)

    current_ep = run_id // n_scenes_of_each_episode
    current_scn = run_id % n_scenes_of_each_episode

    listValidsInvalids = cfg["paths"]["coord_vehicle_txrx"]    
    run = start_run
    C.scene.frame_set(frame_num)     
    if bpy.data.objects.get("Camera") is None:
        print('Creating Camera')
        bpy.ops.object.camera_add()
        D.cameras['Camera'].clip_end = 300
    
    while run < end_run:
        print('Processing run' + str(run) + ' ...') 
        print("Current Episode: ",current_ep)
        print('Current Scene: ', current_scn)
        time_elapsed = datetime.now() - startTime
        scene_path = os.path.join(folder_scanned_name,format_run_name(run)) 
        if not os.path.exists(scene_path):
            print('\nWarning: could not find file ', scene_path , ' Stopping...')
            break
        sumo_info_file = os.path.join(scene_path,'sumoOutputInfoFileName.txt')    
        path_info_file = os.path.join(scene_path,'study/model.paths.t001_01.r002.p2m')
        vPosition = getInfoVehicles(sumo_info_file)
        Position = vPosition
        vectorsPath= getInfoPath(path_info_file, 1)
        animateVehiclesBlender(Position, vehicles_blend_path) 
        get4Photos(listValidsInvalids,folder_img_dataset,current_ep,current_scn,run)
        for obj in D.objects:
            if obj.name.startswith('flow') or obj.name.startswith('_flow'):
                obj.select = True
                bpy.ops.object.delete()
        run += 1
        current_scn += 1
        if current_scn % n_scenes_of_each_episode:
            current_ep +=1
            current_scn = 0
    endAnimation(frame_num)
    time_elapsed = datetime.now() - startTime
    print("Total time elapsed: " + str(time_elapsed))

def getPhoto360(file_path, current_ep, current_scn, run):
    """
    Capture panoramic 360-degree images from receiver vehicles in the Blender scene.

    This function configures the active camera as an equirectangular panoramic
    camera, reads the list of valid receiver vehicles from a CSV file, positions
    the camera above each selected vehicle, and renders a panoramic image for
    the specified simulation run.

    Args:
        file_path: Path to the CSV file containing valid vehicle, episode, and
            scene information.
        current_ep: Current episode index used to filter valid vehicles.
        current_scn: Current scene index used to filter valid vehicles.
        run: Simulation run identifier used to organize the output image path.

    Raises:
        KeyError: If a selected vehicle is not found in the Blender scene.
        FileNotFoundError: If the CSV file specified by ``file_path`` does not exist.
    """

    bpy.context.scene.render.resolution_x = 2000
    bpy.context.scene.render.resolution_y = 1000
    C.scene.render.engine = 'CYCLES'
    scan_vehicles = []
    cam = D.objects['Camera']
    C.scene.camera = cam
    D.cameras['Camera'].type = 'PANO'
    D.cameras['Camera'].cycles.panorama_type = 'EQUIRECTANGULAR'

    with open(file_path) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if current_scn == int(row['SceneID']) and current_ep == int(row['EpisodeID']) and row['Val'] == 'V':
                scan_vehicles.append(row['VehicleName'])    

    for vehicle in scan_vehicles:
        veh = D.objects[vehicle]
        cam.location = (0,0,0)
        #cam.parent = D.objects[vehicle]
        cam.location = veh.location
        cam.location[2] = veh.dimensions[2] + 3
        cam.rotation_euler = (radians(90), 0, veh.rotation_euler[2])
        D.scenes['Scene'].render.filepath = 'D:\Lasse\jamelly\imagesPano\\'+format_run_name(run)+'\\'+vehicle
        print('Taking photo of vehicle ', veh.name)
        bpy.ops.render.render(write_still=True)
        print('Done, continuing...')

def get4Photos(file_path, dataset_path, current_ep, current_scn, run):
    """
    Capture four directional images around each valid receiver vehicle.

    This function reads the list of valid vehicles from a CSV file, places the
    active camera above each selected vehicle, and renders four images by
    rotating the camera in 90-degree increments. The images are saved in the
    User Equipment image output directory for the corresponding simulation run.

    Args:
        file_path: Path to the CSV file containing valid vehicle, episode, and
            scene information.
        dataset_path: Base directory where the rendered images will be saved.
        current_ep: Current episode index used to filter valid vehicles.
        current_scn: Current scene index used to filter valid vehicles.
        run: Simulation run identifier used to organize the output image path.

    Raises:
        KeyError: If a selected vehicle is not found in the Blender scene.
        FileNotFoundError: If the CSV file specified by ``file_path`` does not exist.
    """

    scan_vehicles = []
    cam = D.objects['Camera']
    D.cameras['Camera'].clip_end = 300
    C.scene.camera = cam
    D.scenes['Scene'].render.resolution_x = 1280
    D.scenes['Scene'].render.resolution_y = 720

    with open(file_path) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if current_scn == int(row['SceneID']) and current_ep == int(row['EpisodeID']) and row['Val'] == 'V':
                scan_vehicles.append(row['VehicleName'])    
 
    camera_name = ['front']
    for vehicle in scan_vehicles:
        angle = 0
        veh = D.objects[vehicle]
        cam.location = (0,0,0)
        cam.location = veh.location
        cam.location[2] = veh.dimensions[2] + 3
        cam.rotation_euler = (radians(90), 0, veh.rotation_euler[2])
        while angle < 4:
            D.scenes['Scene'].render.filepath = os.path.join(dataset_path, 'UE',
                                                            f'run{run}', f'Camera_{vehicle}',
                                                            f'{angle}')
            bpy.ops.render.render(write_still=True)
            cam.rotation_euler[2] += radians(90)
            angle+=1

def getInfoPath(path_info_file, Rx_number=0):
    """
    Parse Wireless InSite path information for a specific receiver.

    This function reads a Wireless InSite path output file and extracts the
    sequence of points associated with each propagation ray. When ``Rx_number``
    is greater than zero, only rays associated with the selected receiver are
    kept. Each point is converted to numerical coordinates and receives the
    corresponding ray metric extracted from the path information line.

    Args:
        path_info_file: Path to the Wireless InSite path output file.
        Rx_number: Receiver index used to filter the extracted rays. If set to
            0, rays from all receivers are included. Defaults to 0.

    Returns:
        A dictionary where each key is a ray index and each value is a list of
        path points. Each point contains x, y, and z coordinates followed by the
        associated ray metric.

    Raises:
        FileNotFoundError: If the path information file does not exist.
        ValueError: If the path file contains values that cannot be converted
            to the expected numeric format.
    """

    with open(path_info_file) as pathfile:
        count = 0
        npoints = False
        pathInfoList = {}
        previousLine = ''
        secondLine = ''
        thirdLine = ''
        raysInfoLine = ''
        RxId = 0
        second_l = False
        third_l = False
        RaysOver = True
        RayInfo = 0
        RxRays = 0
        for line in pathfile:
            if(line.startswith('Tx')):
                if RaysOver:
                    Rxinfo = thirdLine.split(' ')
                    try:
                        RxId = int(Rxinfo[0])
                        RxRays = int(Rxinfo[1])
                    except ValueError:
                        RaysOver = False
                    RaysOver = False
                if Rx_number > 0:
                    if RayInfo == RxRays - 1:
                        RaysOver = True
                tmp = line.split('-')
                npoints = len(tmp)
                pathInfoList[count]  = []
                raysInfoLine = previousLine
                RayInfo = int(raysInfoLine.split(' ')[0])
                count += 1
            else:
                if npoints:
                    tmp = line.split(' ')
                    tmp[0] = float(tmp[0])
                    tmp[1] = float(tmp[1])
                    tmp[2] = float(tmp[2])
                    tmp2 = raysInfoLine.split(' ')
                    tmp.append(float(tmp2[2]))
                    if RxId == Rx_number or Rx_number == 0:
                        pathInfoList[count-1].append(tmp)
                    npoints -=1
            if third_l:
                thirdLine = secondLine
            if second_l:
                secondLine = previousLine
                third_l = True
            previousLine = line
            second_l = True
                    
    return pathInfoList

def getInfoVehicles(sumo_info_file):
    """
    Read vehicle position information from a SUMO output CSV file.

    This function parses vehicle position, orientation, dimensions, and receiver
    status from a SUMO-generated CSV file. The reported position is adjusted
    from the vehicle front reference point to the approximate vehicle center
    used by the Blender/InSite scene.

    Args:
        sumo_info_file: Path to the SUMO output CSV file containing vehicle
            information for a simulation scene.

    Returns:
        A dictionary indexed by vehicle ID. Each entry contains the adjusted
        InSite x and y coordinates, vehicle height, angle, receiver status,
        and z coordinate.

    Raises:
        FileNotFoundError: If the SUMO output file does not exist.
        ValueError: If numeric fields such as position, length, or angle cannot
            be converted to floats.
    """
    
    #first rotate and then translate
    with open(sumo_info_file) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='`')
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

def endAnimation(frame_num):
    """
    Hide animated vehicle objects at the end of the animation.

    This function iterates over the Blender scene and hides all objects whose
    names start with ``flow``. Visibility keyframes are inserted so that the
    final hidden state is stored in the animation timeline.

    Args:
        frame_num: Frame number associated with the final animation state.
    """

    for x in range(0, len(bpy.context.scene.objects)):
        obj_name = bpy.context.scene.objects[x].name
        if obj_name.startswith('flow'): # Add to list
            bpy.data.objects[obj_name].hide_render = True
            bpy.data.objects[obj_name].hide = True
            bpy.data.objects[obj_name].keyframe_insert(data_path="hide_render", index=-1)
            bpy.data.objects[obj_name].keyframe_insert(data_path="hide", index=-1)

def animateVehiclesBlender(vPosition, vehicles_blend_path):
    """
    Add, update, and animate vehicles in the Blender scene.

    This function synchronizes the Blender scene with the vehicle positions
    provided in ``vPosition``. Existing vehicle objects are moved and rotated,
    missing objects are imported from the vehicle Blender model file, and
    objects no longer present in the current scene are hidden.

    Args:
        vPosition: Dictionary containing vehicle or pedestrian position data.
            Each entry must include adjusted x and y coordinates, height,
            angle, and z coordinate.
        vehicles_blend_path: Path to the Blender vehicle model file or directory
            used to append car, bus, truck, drone, or pedestrian objects.

    Raises:
        KeyError: If an expected field is missing from a vehicle entry.
        ValueError: If position, height, or angle values cannot be converted to
            floats.
    """
    
    for x in range(0, len(bpy.context.scene.objects)):
        obj_name = bpy.context.scene.objects[x].name
        if obj_name.startswith('flow') or obj_name.startswith('dflow') or obj_name.startswith('ped'): 
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

if __name__ == '__main__':
    main()
