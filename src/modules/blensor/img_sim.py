import sys
import os
import json
import bpy
import csv
import sqlite3
import shutil
import copy
import numpy as np
from bpy import data as D
from bpy import context as C
from mathutils import *
from math import *
from datetime import datetime

def base_run_dir_fn(i): #the folders will be run00001, run00002, etc.
    """returns the `run_dir` for run `i`"""
    return "run{:05d}".format(i)

def main():
    startTime = datetime.now()
    frame_num = 0

    with open('config.json', 'r') as file:
        cfg = json.load(file)

    cur_dir = os.curdir
    folder_scanned_name = os.path.join(cur_dir, 'simulations', cfg['simulation_paths']['results_dir_path'])
    folder_img_dataset = os.path.join(cur_dir, 'sim_data', cfg['simulation_paths']['results_dir_path'], 'images')
    vehicles_blend_path = cfg['blensor_options']['path_to_vehicles']
    start_run = cfg['simulation_parameters']['n_init_run']
    end_run = cfg['simulation_parameters']['n_end_run']
    n_scenes_of_each_episode = cfg['simulation_parameters']['n_scenes_of_each_episode']

    if not os.path.exists(folder_img_dataset):
        os.makedirs(folder_img_dataset)
    # folder_scanned_name = args[args.index('--simulation')+1]
    # vehicles_blend_path = args[args.index('--veh_path')+1]
    # start_run = int(args[args.index('--from_run')+1])
    # end_run = int(args[args.index('--to')+1])

    current_scn = 0
    current_ep = 0
    listValidsInvalids = os.path.join(cur_dir, 'sim_data', cfg['simulation_paths']['results_dir_path'], 'CoordVehicleTxRx.csv')
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
        scene_path = os.path.join(folder_scanned_name,base_run_dir_fn(run)) 
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
    #bpy.ops.wm.quit_blender()

def getPhoto360(file_path,current_ep,current_scn,run):
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
        D.scenes['Scene'].render.filepath = 'D:\Lasse\jamelly\imagesPano\\'+base_run_dir_fn(run)+'\\'+vehicle
        print('Taking photo of vehicle ', veh.name)
        bpy.ops.render.render(write_still=True)
        print('Done, continuing...')

def get4Photos(file_path,dataset_path,current_ep,current_scn,run):
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
    # print(scan_vehicles)
    camera_name = ['front']
    for vehicle in scan_vehicles:
        # print(vehicle)
        angle = 0
        veh = D.objects[vehicle]
        cam.location = (0,0,0)
        #cam.parent = D.objects[vehicle]
        cam.location = veh.location
        cam.location[2] = veh.dimensions[2] + 3
        cam.rotation_euler = (radians(90), 0, veh.rotation_euler[2])
        while angle < 4:
            D.scenes['Scene'].render.filepath = os.path.join(dataset_path, 'UE', f'run{run}', f'Camera_{vehicle}', f'{angle}')
            # D.scenes['Scene'].render.filepath = f'{dataset_path}/imgs/'+str(run)+'/'+'Camera_'+vehicle+'/'+str(angle)
            bpy.ops.render.render(write_still=True)
            cam.rotation_euler[2] += radians(90)
            angle+=1



def getInfoPath(path_info_file, Rx_number = 0):
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
                #ray_number = '%05d' % count
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
    #first rotate and then translate
    with open(sumo_info_file) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='`')
        #line = 0
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

def endAnimation(frame_num):
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

if __name__ == '__main__':
    main()
