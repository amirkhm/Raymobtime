import sys
import os
import bpy
import csv
import blensor
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
    folder_scanned_name = args[args.index('--simulation')+1]
    vehicles_blend_path = args[args.index('--veh_path')+1]
    start_run = int(args[args.index('--from_run')+1])
    end_run = int(args[args.index('--to')+1])
    #for key,scene_path in scenes_path.items():
    frame_num = 0
    frame_step = 1
    # start_run = 0
    # end_run = 3
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
        animateVehiclesBlender(Position,run,frame_step,vehicles_blend_path) 
        doScan(Position,'scans_'+base_run_dir_fn(run))
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
def animateVehiclesBlender(vPosition,frame_num,frame_step,vehicles_blend_path):

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

def doZip(pathdir):
    os.system('zip -r -j %s%s.zip %s'%('scans/',pathdir, pathdir))
    print('zip -r -j %s%s.zip %s'%('scans/',pathdir, pathdir))
    shutil.rmtree(pathdir)
# Perform Scan
def doScan(vPosition,pathdir):
    for camera in vPosition.items():
        if camera[1]['isRx']:
            os.mkdir(pathdir)
            car_to_hide = bpy.data.objects[camera[0]]
            car_to_hide.hide_render = True
            car_to_hide.keyframe_insert(data_path="hide_render", index=-1)
            height = float(camera[1]['height']) + 1; # one meter above the car
            scanner = bpy.data.objects["Camera"]
            scanner.location.xyz = float(camera[1]['xinsite']),float(camera[1]['yinsite']),height # X,Y,Z
            scanner.rotation_euler = (radians(90), radians(0), radians(0))
            blensor.blendodyne.scan_advanced(scanner, rotation_speed = 10.0, 
                                simulation_fps=24, angle_resolution = 0.1728, 
                                max_distance = 120, evd_file= pathdir+'/'+camera[0]+'.pcd',
                                noise_mu=0.0, noise_sigma=0.03, start_angle = 0.0, 
                                end_angle = 360.0, evd_last_scan=True, 
                                add_blender_mesh = False, 
                                add_noisy_blender_mesh = False, world_transformation=scanner.matrix_world)
            car_to_hide.hide_render = False
            print(pathdir+'/'+camera[0]+".pcd")
            os.remove(pathdir+'/'+camera[0])
            doZip(pathdir)
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
