import sys  
import os
import csv
import shutil
import numpy as np
import scipy.spatial.distance as dist
from pypcd import pypcd
from datetime import datetime
import zipfile

def base_run_dir_fn(i):  # the folders will be run00001, run00002, etc.
    """returns the `run_dir` for run `i`"""
    return "scans_run{:05d}".format(i)

def base_vehicle_pcd(flow):  # the folders will be run00001, run00002, etc.
    V_id = float(flow.replace('flow',''))
    #return 'flow{:6f}'.format(V_id)
    return 'flow{}00000'.format(V_id)

def episodes_dict(csv_path):
    with open(csv_path) as csvfile:
        reader = csv.DictReader(csvfile)
        EpisodeInMemory = -1
        SceneInMemory = -1
        episodesDict = {}
        usersDict = {}
        positionsDict = {}
        for row in reader:
            #positions = []
            if str(row['Val']) == 'I':
                continue
            Valid_episode = int(row['EpisodeID'])
            Valid_Scene = int(row['SceneID'])
            Valid_Rx = base_vehicle_pcd(str(row['VehicleName']))
            key_dict = str(Valid_episode) + ',' + str(Valid_Scene)
            #key_dict = [Valid_episode, Valid_Scene]
            if EpisodeInMemory != Valid_episode:
                episodesDict[Valid_episode]  = []
                usersDict[key_dict]  = []
                EpisodeInMemory = Valid_episode
                SceneInMemory = -1
            #csv_output = Valid_Scene + ',' + Valid_Rx
            if SceneInMemory != Valid_Scene:
                episodesDict[Valid_episode]  = []
                usersDict[key_dict]  = []
                SceneInMemory = Valid_Scene
                episodesDict[Valid_episode].append(Valid_Scene)
            Rx_info = [Valid_Rx, float(row['x']), float(row['y']), float(row['z']), int(row['RxID'])]
            usersDict[key_dict].append(Rx_info)
    return episodesDict, usersDict

def gen_lidar_matrix(c):
    startTime = datetime.now()

    print('Check Quantization parameters and Tx position before run!')
    
    main_folder = os.path.join(c.working_directory, 'sim_data', c.sim_name)
    if not os.path.exists(main_folder):
        os.makedirs(main_folder)
        
    fileToRead = os.path.join(main_folder, 'CoordVehicleTxRx.csv')
    
    type_data = c.type_data
    outputFolder = os.path.join(main_folder, f'./lidar_car_matrix_{type_data}')
    if not os.path.exists(outputFolder):
        os.makedirs(outputFolder)

    # Configuration of parameters
    dictvehicle = {1.59 : 5, 3.2 : 9.5, 4.3 : 13} #CarSize/BusSize/TruckSize
    # Quantization parameters
    QP = c.QP
    Tx = c.Tx_position
    max_dist_LIDAR = c.max_dist_LIDAR

    dx = np.arange(QP['Xmin'],QP['Xmax'],QP['Xp'])
    dy = np.arange(QP['Ymin'],QP['Ymax'],QP['Yp'])
    
    #initializing variables
    numScenesPerEpisode = c.time_of_episode #number of scenes per episode
    scans_path = os.path.join(main_folder, 'scans')
    
    runs = c.n_run
    starting_episode = runs[0]/numScenesPerEpisode
    last_episode = runs[-1]/numScenesPerEpisode
    episodeID = int(starting_episode)
    
    total_num_scenes = runs[0] #all processed scenes
    should_stop = False

    #Dicts
    scenes_in_ep, RX_in_ep = episodes_dict(fileToRead)

    if type_data == '3D':
        dz = np.arange(QP['Zmin'],QP['Zmax'],QP['Zp'])
        #Assumes 10 Tx/Rx pairs per scene
        #TO-DO: Support for episodes with more than 1 scene
        zeros_array = np.zeros((10, np.size(dx), np.size(dy), np.size(dz)), np.int8)
    else:
        zeros_array = np.zeros((10, np.size(dx), np.size(dy)), np.int8)

    while not should_stop:

        obstacles_matrix_array = zeros_array

        if episodeID > int(last_episode):
            print('\nLast desired episode ({}) reached'.format(int(last_episode)))
            break

        for s in range(numScenesPerEpisode):
            tmpdir = './tmp/scans'
            if not os.path.exists(tmpdir):
                os.makedirs(tmpdir)
            scans_dir = scans_path + '/' + base_run_dir_fn(total_num_scenes) + '.zip'
            key_dict = str(episodeID) + ',' + str(s)
            RxFlow = RX_in_ep[key_dict]
            

            if not os.path.exists(scans_dir):
                print('\nWarning: could not find file ', scans_dir, ' Stopping...')
                should_stop = True
                break

            with zipfile.ZipFile(scans_dir, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
            for vehicle in RxFlow:
                if os.path.exists(tmpdir + '/' + vehicle[0] + '.pcd'):
                    pcd_path = tmpdir + '/' + vehicle[0] + '.pcd'
                elif os.path.exists(tmpdir + '/' + vehicle[0] + '0.pcd'):
                    pcd_path = tmpdir + '/' + vehicle[0] + '0.pcd'
                elif os.path.exists(tmpdir + '/' + vehicle[0] + '00.pcd'):
                    pcd_path = tmpdir + '/' + vehicle[0] + '00.pcd'
                pc = pypcd.PointCloud.from_path(pcd_path)

                vehicle_position = [[vehicle[1],vehicle[2],vehicle[3]]]

                #Filter1 : Removing Floor 
                ind = np.where(pc.pc_data['z'] > 0.2)
                fCloud = pc.pc_data[ind]
                tmpCloud = [[i['x'], i['y'], i['z']] for i in fCloud]

                #Filter2: Removing every obstacle bigger than max_dist_LIDAR
                D = dist.cdist(vehicle_position,tmpCloud,'euclidean')
                ind2 = np.where(D[0] < max_dist_LIDAR) # MaxSizeLIDAR
                fffCloud = fCloud[ind2]

                indx = quantizeJ(fffCloud['x'],dx)
                indx = [int(i) for i in indx]
                indy = quantizeJ(fffCloud['y'],dy)
                indy = [int(i) for i in indy]

                Rx_q_indx = quantizeJ([vehicle[1]],dx)
                Rx_q_indy = quantizeJ([vehicle[2]],dy)
                Tx_q_indx = quantizeJ([Tx[0]],dx)
                Tx_q_indy = quantizeJ([Tx[1]],dy)
                

                if type_data == '3D':
                    indz = quantizeJ(fffCloud['z'],dz)
                    indz = [int(i) for i in indz]
                    Rx_q_indz = quantizeJ([vehicle[3]],dz)
                    Tx_q_indz = quantizeJ([Tx[2]],dz)
                    MD = np.zeros((np.size(dx),np.size(dy),np.size(dz)))
                else:
                    MD = np.zeros((np.size(dx),np.size(dy)))

                # Obstacles = 1
                for i in range(len(indx)):
                    if type_data == '3D':
                        MD[indx[i],indy[i],indz[i]] = 1
                    else:
                        MD[indx[i],indy[i]] = 1
                
                # Tx -1 Rx -2
                if type_data == '3D':         
                    MD[int(Tx_q_indx[0]),int(Tx_q_indy[0]),int(Tx_q_indz[0])] = -1
                    MD[int(Rx_q_indx[0]),int(Rx_q_indy[0]),int(Rx_q_indz[0])] = -2
                else:
                    MD[int(Tx_q_indx[0]),int(Tx_q_indy[0])] = -1
                    MD[int(Rx_q_indx[0]),int(Rx_q_indy[0])] = -2
                
                obstacles_matrix_array[int(vehicle[4]), :] = MD
                time_elapsed = datetime.now() - startTime
                #print("Time elapsed: " + str(time_elapsed))
            
            total_num_scenes += 1
            shutil.rmtree(tmpdir)

        npz_name = os.path.join(outputFolder , 'obstacles_e_' + str(episodeID) + '.npz')
        print('==> Wrote file ' + npz_name)
        np.savez_compressed(npz_name, obstacles_matrix_array=obstacles_matrix_array)
        print('Saved file ', npz_name)

        time_elapsed = datetime.now() - startTime
        print("Total time elapsed: " + str(time_elapsed))
        episodeID += 1


def quantizeJ(signal, partitions):
    xmin = min(signal)
    xmax = max(signal)
    M = len(partitions)
    delta = partitions[2] - partitions[1]
    quantizerLevels = partitions
    xminq = min(quantizerLevels)
    xmaxq = max(quantizerLevels)
    x_i = (signal-xminq) / delta #quantizer levels
    x_i = np.round(x_i)
    ind = np.where(x_i < 0)
    x_i[ind] = 0
    ind = np.where(x_i>(M-1))
    x_i[ind] = M-1; #impose maximum
    x_q = x_i * delta + xminq;  #quantized and decoded output

    return list(x_i)