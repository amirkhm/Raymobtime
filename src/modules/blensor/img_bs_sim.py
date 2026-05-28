import os
import json
import bpy
import csv
import shutil
import copy
import numpy as np
from bpy import data as D
from bpy import context as C
from mathutils import *
from math import *
from datetime import datetime
from zipfile import ZipFile
from src.scripts.helpers import format_run_name

def main():
    startTime = datetime.now()

    with open('config.json', 'r') as file:
        cfg = json.load(file)

    cur_dir = os.curdir
    folder_scanned_name = os.path.join(cur_dir, 'simulations', cfg['simulation_paths']['results_dir_path'])
    folder_img_dataset = os.path.join(cur_dir, 'sim_data', cfg['simulation_paths']['results_dir_path'], 'images')
    vehicles_blend_path = cfg['blensor_options']['path_to_vehicles']
    start_run = cfg['simulation_parameters']['n_init_run']
    end_run = cfg['simulation_parameters']['n_end_run']

    if not os.path.exists(folder_img_dataset):
        os.makedirs(folder_img_dataset)

    useRays = False
    usePed = False

    c = 0
    frame_num = 0
    frame_step = 1
    run = start_run
    camera_n = cfg['blensor_options']['img_simulation_options']['n_camera_BS']
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
    scene = C.scene
    try:
        cam = D.objects[camera]
    except:
        raise NameError(f"\n\nERROR: object camera '{camera}' not found, try following the naming pattern CameraN in blender scenario")
    scene.camera = cam
    scene.render.filepath = os.path.join(output_folder_name, 'BS', f'run{run}', f'{camera}')
    bpy.ops.render.render(write_still = True)
    
def classifyRays(pathInfoList,  numCl=2):
    raysCl = {}
    cleanPathInfo = {}

    # Get Info part
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


def getInfoPath(path_info_file):
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
            vPosition[row['veh']] = {'xinsite':str(float(row['xinsite']) - deltaX),'yinsite':str(float(row['yinsite']) - deltaY),'height':row[' height'],'angle':row['angle'],'isRx':row['isRx'], 'z3':row['z3']}

    return vPosition

def getInfoPedestrian(info_file):
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
    for rays in vectorsPath.items():
        objname = str(frame_num)+'Ray'+str('%05d' % rays[0])
        createLineBlender(objname,rays[1], frame_num, frame_step)


def endRayAnimation(frame_num, frame_step):
    bpy.context.scene.frame_set(frame_num + frame_step)
    for x in range(0, len(bpy.context.scene.objects)):
        obj_name = bpy.context.scene.objects[x].name
        if obj_name.startswith(str(frame_num)): # Add to list
            bpy.data.objects[obj_name].hide_render = True
            bpy.data.objects[obj_name].hide = True
            bpy.data.objects[obj_name].keyframe_insert(data_path="hide_render", index=-1)
            bpy.data.objects[obj_name].keyframe_insert(data_path="hide", index=-1)

def endAnimation(frame_num):
    bpy.context.scene.frame_set(0)
    for x in range(0, len(bpy.context.scene.objects)):
        obj_name = bpy.context.scene.objects[x].name
        if obj_name.startswith('flow'): # Add to list
            bpy.data.objects[obj_name].hide_render = True
            bpy.data.objects[obj_name].hide = True
            bpy.data.objects[obj_name].keyframe_insert(data_path="hide_render", index=-1)
            bpy.data.objects[obj_name].keyframe_insert(data_path="hide", index=-1)

# se n existir, cria
# se existir, movimenta
# se existia e n existe mais retirar
def animateVehiclesBlender(vPosition, vehicles_blend_path):
    bpy.context.scene.frame_set(0)

    # Pre processamento dos que estao na cena
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


# Escolhe o angulo para rotacionar que tem a menor diferença de angulo com o angulo anterior
def chooseAngleToRotate(previousAngle, nextAngle):
    cw = nextAngle - previousAngle
    ccw = - cw
    cw360 = convert360(cw)
    ccw360 = convert360(ccw)
    if ( cw360 < ccw360 ) :
        return previousAngle + cw360
    else:
        return previousAngle - ccw360


def convert360(x):
    if ( x < 0 ) :
        n = ceil(-x / 360)
        x = x + n*360

    return x % 360

def buildVehiclesBlender(vPosition):
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
        veh.location.xyz = float(vehicles[1]['xinsite']),float(vehicles[1]['yinsite']),0#float(vehicles[1]['height'])/2 # X,Y,Z


# Build vehicles in Blender
def buildVehiclesBlenderBox(vPosition):
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
    os.system('zip %s.zip -r -j %s'%(pathdir, pathdir))
    print('zip %s.zip -r -j %s'%(pathdir, pathdir))
    shutil.rmtree(pathdir)
# Perform Scan
def doScan(vPosition,pathdir):
    for camera in vPosition.items():
        if camera[1]['isRx']:
            os.mkdir(pathdir)
            car_to_hide = bpy.data.objects[camera[0]]
            car_to_hide.hide_render = True
            height = float(camera[1]['height']) + 1; # one meter above the car
            scanner = bpy.data.objects["Camera"]
            scanner.location.xyz = float(camera[1]['xinsite']),float(camera[1]['yinsite']),height # X,Y,Z
            scanner.rotation_euler = (radians(90), radians(0), radians(0))
            blensor.blendodyne.scan_advanced(scanner, rotation_speed = 10.0,simulation_fps=24, angle_resolution = 0.1728, max_distance = 120, evd_file= pathdir+'/'+camera[0]+".pcd",noise_mu=0.0, noise_sigma=0.03, start_angle = 0.0, end_angle = 360.0, evd_last_scan=True, add_blender_mesh = False,add_noisy_blender_mesh = False, world_transformation=scanner.matrix_world)
            car_to_hide.hide_render = False
            print(pathdir+'/'+camera[0]+".pcd")
            doZip(pathdir)
            myfile = pathdir+'/'+camera[0]
            '''doClean(myfile)'''
    doZip(pathdir)

# Perform Scan
def doZipPython(filepath):
    with ZipFile(filepath+'Zipped.zip', 'w') as zipped:
        for folderName, subfolders, filenames in os.walk(filepath):
            for filename in filenames:
                filePath = os.path.join(folderName, filename)
                zipped.write(filePath)
                print('Write '+filePath)
    shutil.rmtree(filepath)

def doClean(myfile):
## If file exists, delete it ##
    if os.path.isfile(myfile):
        os.remove(myfile)
    else:    ## Show an error ##
        print("Error: %s file not found" % myfile)

if __name__ == '__main__':
    main()
