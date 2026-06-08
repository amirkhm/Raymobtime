import sys
import shutil
import os
import json
import bpy
import csv
import copy
import numpy as np
from math import *

def load_runtime_config():
    """
    Load the runtime configuration passed by blensor_src.py.

    Expected command format:
        blender scenario.blend --background -P script.py -- run_id config_path

    Example:
        -- 5 /tmp/raymobtime_blensor_run_00005.json
    """
    args = sys.argv

    if "--" not in args:
        raise RuntimeError(
            "Missing '--' in Blender command arguments. "
            "Expected: -- run_id config_path"
        )

    user_args = args[args.index("--") + 1:]

    if len(user_args) < 2:
        raise RuntimeError(
            "Expected arguments after '--': run_id config_path"
        )

    run_id = int(user_args[0])
    config_path = user_args[1]

    with open(config_path, "r", encoding="utf-8") as file:
        cfg = json.load(file)

    return run_id, cfg

def getInfoPath(path_info_file):

    """
    Parse Wireless InSite path information from a ray-tracing output file.

    This function reads a Wireless InSite `.p2m` path file and extracts the
    sequence of points associated with each propagation ray. A new ray path is
    detected whenever a line starts with `Tx`. The previous line is used to
    retrieve additional ray information, such as the received power or path gain,
    which is appended to each path point.

    Args:
        path_info_file: Path to the Wireless InSite path output file to be parsed.

    Returns:
        A dictionary where each key is a ray index and each value is a list of
        points that describe the corresponding propagation path. Each point
        contains the x, y, and z coordinates followed by the associated ray
        metric extracted from the path information line.
    """

    with open(path_info_file) as pathfile:
        count = 0
        npoints = False
        pathInfoList = {}
        previousLine = ''
        raysInfoLine = ''
        for line in pathfile:
            if(line.startswith('Tx')):
                tmp = line.split('-')
                npoints = len(tmp)
                ray_number = '%05d' % count
                pathInfoList[count]  = []
                raysInfoLine = previousLine
                count += 1
            else:
                if npoints:
                   tmp = line.split(' ')
                   tmp[0] = float(tmp[0])
                   tmp[1] = float(tmp[1])
                   tmp[2] = float(tmp[2])
                   tmp2 = raysInfoLine.split(' ')
                   tmp.append(float(tmp2[2]))
                   pathInfoList[count-1].append(tmp)
                   npoints -=1
            previousLine = line

    return pathInfoList

def getInfoVehicles(sumo_info_file):
    """
    Read vehicle position information from a SUMO output CSV file.

    This function parses vehicle identifiers, positions, dimensions, orientation,
    receiver status, and transmitter status from a SUMO-generated CSV file. The
    reported SUMO/InSite position is adjusted from the vehicle front reference
    point to the approximate vehicle center by using the vehicle length and
    heading angle.

    Args:
        sumo_info_file: Path to the SUMO output CSV file containing vehicle
            information for a simulation scene.

    Returns:
        A dictionary indexed by vehicle ID. Each entry contains the adjusted
        InSite x and y coordinates, vehicle height, angle, receiver flag,
        transmitter flag, and z coordinate.

    Raises:
        FileNotFoundError: If the SUMO output file does not exist.
        KeyError: If one of the expected CSV columns is missing.
        ValueError: If numeric fields such as position, length, or angle cannot
            be converted to floats.
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
            if(row['transmitterIndex'] != '-1'):
                isTx = True
            thisAngleInRad = np.radians(float(row['angle'])) #*np.pi/180
            deltaX = (float(row['length'])/2.0) * np.sin(thisAngleInRad)
            deltaY = (float(row['length'])/2.0) * np.cos(thisAngleInRad)
            vPosition[row['object_id']] = {'xinsite':str(float(row['xinsite']) - deltaX),'yinsite':str(float(row['yinsite']) - deltaY),'height':row['height'],'angle':row['angle'],'isRx':isRx, 'isTx':isTx, 'z3':row['z3']}
        
    return vPosition

def endAnimation(frame_num):
    """
    Hide animated vehicle objects at the end of the Blender animation.

    This function sets the current Blender frame to ``frame_num`` and hides all
    scene objects whose names start with ``flow``. Visibility keyframes are
    inserted so that the final hidden state is stored in the animation timeline.

    Args:
        frame_num: Frame number where the final visibility state should be set.
    """
    bpy.context.scene.frame_set(frame_num)
    for x in range(0, len(bpy.context.scene.objects)):
        obj_name = bpy.context.scene.objects[x].name
        if obj_name.startswith('flow'): # Add to list
            bpy.data.objects[obj_name].hide_render = True
            bpy.data.objects[obj_name].hide = True
            bpy.data.objects[obj_name].keyframe_insert(data_path="hide_render", index=-1)
            bpy.data.objects[obj_name].keyframe_insert(data_path="hide", index=-1)

def animateVehiclesBlender(vPosition, vehicles_blend_path):
    """
    Add, update, hide, and animate vehicle objects in the Blender scene.

    This function synchronizes the Blender scene with the vehicle positions
    provided in ``vPosition``. Objects already present in the scene are updated
    with the current position and rotation. Missing objects are appended from
    the vehicle Blender model library according to their height, and objects
    that are no longer present in the current simulation step are hidden and
    renamed.

    Args:
        vPosition: Dictionary containing vehicle position and metadata. Each
            entry must include adjusted x and y coordinates, height, angle,
            receiver/transmitter flags, and z coordinate.
        vehicles_blend_path: Path to the Blender vehicle model library used to
            append car, bus, truck, drone, or pedestrian objects.

    Raises:
        KeyError: If a required vehicle field is missing from ``vPosition``.
        ValueError: If position, height, or angle values cannot be converted to
            floats.
    """

    bpy.context.scene.frame_set(0)
    # Pre-process the scene by hiding all existing vehicle objects that are not present in the current simulation step.    objects_in_scene = []
    for x in range(0, len(bpy.context.scene.objects)):
        obj_name = bpy.context.scene.objects[x].name
        if obj_name.startswith('flow') or obj_name.startswith('droneFlow') or obj_name.startswith('ped'): # Add to list

            if not obj_name in vPosition:
                bpy.data.objects[obj_name].hide_render = True
                bpy.data.objects[obj_name].hide = True
                bpy.data.objects[obj_name].keyframe_insert(data_path="hide_render", index=-1)
                bpy.data.objects[obj_name].keyframe_insert(data_path="hide", index=-1)
                bpy.data.objects[obj_name].name = '_'+bpy.data.objects[obj_name].name
    for vehicles in vPosition.items():
        if bpy.data.objects.get(vehicles[0]) is not None: 
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

def chooseAngleToRotate(previousAngle, nextAngle):
    """
    Select the shortest rotation direction between two angles.

    This function computes the clockwise and counterclockwise angular distances
    between the previous and next angles and returns the updated angle using
    the smallest rotation.

    Args:
        previousAngle: Current object rotation angle in degrees.
        nextAngle: Target object rotation angle in degrees.

    Returns:
        The adjusted angle that reaches the target orientation using the
        shortest rotation direction.
    """

    cw = nextAngle - previousAngle
    ccw = - cw
    cw360 = convert360(cw)
    ccw360 = convert360(ccw)
    if ( cw360 < ccw360 ) :
        return previousAngle + cw360
    else:
        return previousAngle - ccw360
    
def convert360(x):
    """
    Convert an angle to its equivalent within the [0, 360) degree range.
    """
    if ( x < 0 ) :
        n = ceil(-x / 360)
        x = x + n*360

    return x % 360

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
    else:    
        print("Error: %s file not found" % myfile)

def doZip(pathdir):
    """
    Compress a scan output directory into a ZIP file and remove the original folder.

    The generated ZIP file is saved inside the ``scans`` directory. After the
    compression command is executed, the original scan directory is deleted to
    reduce disk usage.

    Args:
        pathdir: Path to the directory containing scan files to be compressed.

    Raises:
        FileNotFoundError: If the directory to be compressed does not exist.
    """

    os.system('zip -r -j %s%s.zip %s'%('scans/',pathdir, pathdir))
    print('zip -r -j %s%s.zip %s'%('scans/',pathdir, pathdir))
    shutil.rmtree(pathdir)

def classifyRays(pathInfoList,  numCl=2):
    
    """
    Filter ray paths by limiting the number of rays associated with each receiver location.

    This function groups rays according to their receiver location, extracted from
    the last point of each ray path. For each unique receiver location, only the
    first `numCl` rays are kept in the returned dictionary. The received power or
    path gain value is read from the fourth element of the receiver location entry
    before the location is converted into a grouping key.

    Args:
        pathInfoList: Dictionary containing ray path information. Each key
            represents a ray identifier, and each value is a list of path points.
            The last point is expected to contain the receiver coordinates and
            an associated received power or gain value.
        numCl: Maximum number of rays to keep for each unique receiver location.
            Defaults to 2.

    Returns:
        A dictionary containing the filtered ray path information, preserving the
        original ray identifiers for the selected rays.
    """

    raysCl = {}
    cleanPathInfo = {}

    for rays in pathInfoList.items():
        RxLocation = copy.deepcopy( rays[1][len(rays[1])-1] )
        dbRx = RxLocation[3]
        RxLocation.pop()
        for i in range(len(RxLocation)):
            RxLocation[i] = str(RxLocation[i])
        key = ' '.join(RxLocation)
        if key in raysCl:
            count += 1
            raysCl[key].append(dbRx)
        else:
            count = 0
            raysCl[key] = [dbRx]
        if count < numCl:
            cleanPathInfo[rays[0]] = rays[1]

    return cleanPathInfo