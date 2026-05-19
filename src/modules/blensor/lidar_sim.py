import sys
import os
import json
import bpy
import csv
import src.modules.blensor as blensor
import shutil
import numpy as np
from bpy import data as D
from bpy import context as C
from mathutils import *
from math import *
from datetime import datetime

def base_run_dir_fn(i): #the folders will be run00001, run00002, etc.
    """returns the `run_dir` for run `i`"""
    return "run{:05d}".format(i)

def simulator():
    startTime = datetime.now()
    # Get infos from the args
    args = sys.argv

    with open('config.json', 'r') as file:
        cfg = json.load(file)

    cur_dir = os.curdir
    folder_scanned_name = os.path.join(cur_dir, 'simulations', cfg['simulation_paths']['results_dir_path'])
    folder_scans_dataset = os.path.join(cur_dir, 'sim_data', cfg['simulation_paths']['results_dir_path'], 'scans')
    vehicles_blend_path = cfg['blensor_options']['path_to_vehicles']
    start_run = cfg['simulation_parameters']['n_init_run']
    end_run = cfg['simulation_parameters']['n_end_run']

    if not os.path.exists(folder_scans_dataset):
        os.makedirs(folder_scans_dataset)
    #for key,scene_path in scenes_path.items():
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
        scene_path = os.path.join(folder_scanned_name,base_run_dir_fn(run)) 
        if not os.path.exists(scene_path):
            print('\nWarning: could not find file ', scene_path , ' Stopping...')
            break
        sumo_info_file = os.path.join(scene_path,'sumoOutputInfoFileName.txt')
        #path_info_file = os.path.join(scene_path,'study/model.paths.t001_01.r002.p2m')
        vPosition = getInfoVehicles(sumo_info_file)
        Position = vPosition
        animateVehiclesBlender(Position, vehicles_blend_path) 
        doScan(Position,'scans_'+base_run_dir_fn(run), folder_scans_dataset)
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
    """Remove all objects, materials, textures, etc."""
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
            isRx = False
            isTx = False
            if(row['receiverIndex'] != '-1'):
                isRx = True
            if(row['transmitterIndex'] != '-1'):
                isTx = True
            thisAngleInRad = np.radians(float(row['angle'])) #*np.pi/180
            deltaX = (float(row['length'])/2.0) * np.sin(thisAngleInRad)
            deltaY = (float(row['length'])/2.0) * np.cos(thisAngleInRad)
            vPosition[row['veh']] = {'xinsite':str(float(row['xinsite']) - deltaX),'yinsite':str(float(row['yinsite']) - deltaY),'height':row[' height'],'angle':row['angle'],'isRx':isRx, 'isTx':isTx, 'z3':row['z3']}
        
    return vPosition

def endAnimation(frame_num):
    bpy.context.scene.frame_set(frame_num)
    for x in range(0, len(bpy.context.scene.objects)):
        obj_name = bpy.context.scene.objects[x].name
        if obj_name.startswith('flow'): # Add to list
            #objects_in_scene.append(obj_name)
            #bpy.data.objects[obj_name].select = True
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
            #objects_in_scene.append(obj_name)
            #if not obj_name in vPosition:
            if not obj_name in vPosition:
                #print("Hiding",obj_name,"in Frame number:",frame_num)
                #bpy.data.objects[obj_name].select = True
                bpy.data.objects[obj_name].hide_render = True
                bpy.data.objects[obj_name].hide = True
                bpy.data.objects[obj_name].keyframe_insert(data_path="hide_render", index=-1)
                bpy.data.objects[obj_name].keyframe_insert(data_path="hide", index=-1)
                bpy.data.objects[obj_name].name = '_'+bpy.data.objects[obj_name].name
    for vehicles in vPosition.items():
        if bpy.data.objects.get(vehicles[0]) is not None: # Existe, code to move
            #print("found object")
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

def doZip(pathdir, scans_output):
    zip_output = os.path.join(scans_output, pathdir)
    cmd = f"zip -r -j {zip_output}.zip {pathdir}"
    # os.system('zip -r -j %s%s.zip %s'%('scans/',pathdir, pathdir))
    # print('zip -r -j %s%s.zip %s'%('scans/',pathdir, pathdir))
    os.system(cmd)
    print(cmd)
    shutil.rmtree(pathdir)
# Perform Scan
def doScan(vPosition,pathdir, scans_output):
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
    #doZip(pathdir)
        
# Perform Scan
def doClean(myfile):
## If file exists, delete it ##
    if os.path.isfile(myfile):
        os.remove(myfile)
    else:    ## Show an error ##
        print("Error: %s file not found" % myfile)

if __name__ == "__main__":
    simulator()
