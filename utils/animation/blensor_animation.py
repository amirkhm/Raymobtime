import sys  
import os
import bpy
import csv
import sqlite3
import blensor
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
    blend_city = 'rosslyn.blend'
    blend_vehicles = 'vehicles.blend'
    useRays = True	
    usePed = False
    argv = sys.argv
   # if len(argv) != 6:
   #     print('You need to specify the folder that has the output files written by the simulator!')
   #     #print('Usage: python', argv[0], 'input_folder')
   #     print('Usage: blender <blenderfile>.blend -b -P ', argv[3], ' -- input_folder')
   #     exit(-1)
    argv = argv[argv.index("--") + 1:]
   #To indicate the input folder position
    folder_scanned_name = argv[0]
    c = 0
    # veh = None
    #for key,scene_path in scenes_path.items():
    step = 0
    frame_num = 0
    frame_step = 1
    start_run = 0
    end_run = 47
    run = start_run
    bpy.data.scenes['Scene'].frame_end = end_run-1
    bpy.data.scenes['Scene'].frame_start = 0
    while run<end_run:
        print('Processing run' + str(run) + ' ...') 
        time_elapsed = datetime.now() - startTime
        scene_path = os.path.join(folder_scanned_name,format_run_name(run)) 
        if not os.path.exists(scene_path):
            print('\nWarning: could not find file ', scene_path , ' Stopping...')
            break
        sumo_info_file = os.path.join(scene_path,'sumoOutputInfoFileNamePed.txt')
        if usePed:
            sumo_ped_info_file = os.path.join(scene_path,'sumoOutputInfoFileNamePed.txt')

        path_info_file = os.path.join(scene_path,'study/model.paths.t001_01.r002.p2m')
        
        vPosition = getInfoPedestrian(sumo_info_file)
        
        if usePed:
            vPedPosition = getInfoPedestrian(sumo_ped_info_file)
            Position = dict(vPosition, **vPedPosition)
        else:
            Position = vPosition
        vectorsPath= getInfoPath(path_info_file) 
        nVectorsPath = classifyRays(vectorsPath, 15)

        if step<3:
            step+=1
        else:
            step=1
            

        animateVehiclesBlender(Position,run,frame_step,step)
        doScan(vPosition, '/home/fritz/data/raymobtime/Animation/animation/saida/resultado'+str(run))
        for obj in D.objects:
            if obj.name.startswith('flow') or obj.name.startswith('_flow'):
                obj.select = True
                bpy.ops.object.delete()
        #buildVehiclesBlender(vPosition)
        #buildVehiclesBlenderBox(vPosition)
        if useRays:
            rayAnimation(nVectorsPath,frame_num,frame_step)
            endRayAnimation(frame_num,frame_step)
        run += 1
        frame_num += frame_step

    #sys.exit('stop')
    endAnimation(frame_num)
    time_elapsed = datetime.now() - startTime
    print("Total time elapsed: " + str(time_elapsed))
    #bpy.ops.wm.quit_blender()

def classifyRays(pathInfoList,  numCl=2):
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
                #print(count)
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
            vPosition[row['object_id']] = {'xinsite':str(float(row['xinsite']) - deltaX),
                                     'yinsite':str(float(row['yinsite']) - deltaY),
                                     'height':row['height'],'angle':row['angle'],
                                     'isRx':row['isRx'], 'z3':row['z3']}
        
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
            vPosition[row['ped']] = {'xinsite':str(float(row['xinsite']) - deltaX),'yinsite':str(float(row['yinsite']) - deltaY),'height':str(1.72),'angle':row['angle'],'isRx':row['isRx'], 'z3':0}
        
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
    objectdata.data.extrude = 0.005
    objectdata.data.bevel_depth = 0.01

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
            #objects_in_scene.append(obj_name)
            #bpy.data.objects[obj_name].select = True
            bpy.data.objects[obj_name].hide_render = True
            bpy.data.objects[obj_name].hide = True
            bpy.data.objects[obj_name].keyframe_insert(data_path="hide_render", index=-1)
            bpy.data.objects[obj_name].keyframe_insert(data_path="hide", index=-1)

def endAnimation(frame_num):
    bpy.context.scene.frame_set(0)
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
# se existia e n existe mais retiraruseRays
def animateVehiclesBlender(vPosition,frame_num,frame_step,step):
    
    # print(vPosition)
    # print(frame_num)
    # print(frame_step)
    # sys.exit('stop')
    step =str(step)

    bpy.context.scene.frame_set(frame_num)
    # global veh
    #print(frame_num)
    # deselect all
    #bpy.ops.object.select_all(action='DESELECT')
    # Pre processamento dos que estao na cena
    objects_in_scene = []
    i = 0
    
    for x in range(0, len(bpy.context.scene.objects)):
        
        obj_name = bpy.context.scene.objects[x].name
        if obj_name.startswith('flow') or obj_name.startswith('droneFlow') or obj_name.startswith('ped'): # Add to list
            #objects_in_scene.append(obj_name)
            #if not obj_name in vPosition:
            i = i + 1
            if not obj_name in vPosition:
                #print("Hiding",obj_name,"in Frame number:",frame_num)
                #bpy.data.objects[obj_name].select = True
                bpy.data.objects[obj_name].hide_render = True
                bpy.data.objects[obj_name].hide = True
                bpy.data.objects[obj_name].keyframe_insert(data_path="hide_render", index=-1)
                bpy.data.objects[obj_name].keyframe_insert(data_path="hide", index=-1)
                bpy.data.objects[obj_name].name = '_'+bpy.data.objects[obj_name].name
                
    #print(i)
    #bpy.ops.object.delete()
    #mat = bpy.data.materials.new("PKHG")
    #mat.diffuse_color = (1,0,0)
    #mat2 = bpy.data.materials.new("PKHG")
    #mat2.diffuse_color = (1.0,1.0,0)
    #mat3 = bpy.data.materials.new("PKHG")
    #mat3.diffuse_color = (0,1.0,0.082)
    #mat4 = bpy.data.materials.new("PKHG")
    #mat4.diffuse_color = (1.01,0,0.1)
    
    #print(vPosition.items())
    
    
    for vehicles in vPosition.items():
        #print(vehicles)
        #print(vehicles[0])
        if bpy.data.objects.get(vehicles[0]) is not None: # Existe, code to move
            #print("found object")
            veh = bpy.data.objects[vehicles[0]]
            #print("oláaaaaaa")
        else:
            if (float(vehicles[1]['height']) == 1.72): # Car
                bpy.ops.wm.append(directory=os.getcwd().replace('/','//') + "//vehicles.blend/Object/", filepath="vehicles.blend", filename=f"pedestrian_step{step}")
                veh = bpy.data.objects[f"pedestrian_step{step}"]
                #veh.active_material = mat
            elif (float(vehicles[1]['height']) == 3.2): # Bus
                bpy.ops.wm.append(directory=os.getcwd().replace('/','//') + "//vehicles.blend/Object/", filepath="vehicles.blend", filename="Bus")
                veh = bpy.data.objects["Bus"]
                #veh.active_material = mat2
            elif (float(vehicles[1]['height']) == 4.3): # Truck
                bpy.ops.wm.append(directory= os.getcwd().replace('/','//') + "//vehicles.blend/Object/", filepath="vehicles.blend", filename="Truck")
                veh = bpy.data.objects["Truck"]
                #veh.active_material = mat3
            elif (float(vehicles[1]['height']) == 0.295): # Drone
                bpy.ops.wm.append(directory= os.getcwd().replace('/','//') + "//vehicles.blend/Object/", filepath="vehicles.blend", filename="Drone")
                veh = bpy.data.objects["Drone"]
            else:
                continue
            
            
            
            veh.name = vehicles[0]
            
            # print(vehicles)
            # print(veh.name)
            # sys.exit('stop')
            # Codigo para limpar frames anteriores
            for i in range(0,frame_num,frame_step):
                bpy.context.scene.frame_set(i)
                veh.hide_render = True
                veh.hide = True
                veh.keyframe_insert(data_path="hide_render", index=-1)
                veh.keyframe_insert(data_path="hide", index=-1)

        bpy.context.scene.frame_set(frame_num)
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
    # global veh
    for vehicles in vPosition.items():
        # veh = None
        if (float(vehicles[1]['height']) == 1.72): # Car
            bpy.ops.wm.append(directory=os.getcwd().replace('/','//') + "//vehicles.blend/Object/", filepath="vehicles.blend", filename="Pedestrian") 
            veh = bpy.data.objects["Pedestrian"]
        elif (float(vehicles[1]['height']) == 3.2): # Bus
            bpy.ops.wm.append(directory=os.getcwd().replace('/','//') + "//vehicles.blend/Object/", filepath="vehicles.blend", filename="Bus")
            veh = bpy.data.objects["Bus"]
        elif (float(vehicles[1]['height']) == 4.3): # Truck
            bpy.ops.wm.append(directory= os.getcwd().replace('/','//') + "//vehicles.blend/Object/", filepath="vehicles.blend", filename="Truck")
            veh = bpy.data.objects["Truck"]
        # elif (float(vehicles[1]['height']) == 0.295): # Drone
        #         bpy.ops.wm.append(directory= os.getcwd().replace('/','//') + "//vehicles.blend/Object/", filepath="vehicles.blend", filename="Drone")
        #         veh = bpy.data.objects["Drone"]
        else:
            continue
        veh.name = vehicles[0]
        veh.hide = False
        veh.hide_render = False
        veh.rotation_euler = (radians(0), radians(0), radians(90-float(vehicles[1]['angle'])))
        veh.location.xyz = float(vehicles[1]['xinsite']),float(vehicles[1]['yinsite']),0#float(vehicles[1]['height'])/2 # X,Y,Z
        veh.keyframe_insert(data_path="hide_render", index=-1)
        veh.keyframe_insert(data_path="hide", index=-1)
        veh.keyframe_insert(data_path="location", index=-1)
        veh.keyframe_insert(data_path="rotation_euler", index=-1)

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

# def doZip(pathdir):
#     os.system('zip %s.zip -r -j %s'%(pathdir, pathdir))
#     print('zip %s.zip -r -j %s'%(pathdir, pathdir))
#     shutil.rmtree(pathdir)

def doZip(pathdir):
    if os.path.exists(pathdir):
        os.system('zip %s.zip -r -j %s' % (pathdir, pathdir))
        print('zip %s.zip -r -j %s' % (pathdir, pathdir))
        if os.path.exists(pathdir):  # Verifica novamente antes de remover
            shutil.rmtree(pathdir)
        else:
            print(f"O diretório {pathdir} não existe, nada para remover.")
    else:
        print(f"O diretório {pathdir} não existe, nada para compactar.")

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
        
def doZipPython(filepath):
    with ZipFile(filepath+'Zipped.zip', 'w') as zipped:
        for folderName, subfolders, filenames in os.walk(filepath):
            for filename in filenames:
                filePath = os.path.join(folderName, filename)
                zipped.write(filePath)
                print('Write '+filePath)
    shutil.rmtree(filepath)

if __name__ == '__main__':
    main()
