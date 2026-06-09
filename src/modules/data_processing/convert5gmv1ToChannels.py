import datetime
import numpy as np
from shapely import geometry
import h5py
import os
import gc
from itertools import islice
from src.modules.data_processing import save5gmdata as fgdb
from src.modules.data_processing import (
    save5gmdata_IsolatedSim as fgdbIS
)

def gen_rays_dataset(c):
    '''
    Will parse all database and create numpy arrays that represent all channels in the database.
    Specificities: some episodes do not have all scenes. And some scenes do not have all receivers.
    Assuming Ne episodes, with Ns scenes each, and Nr receivers (given there was only one transmitter),
    there are Ne x Ns x Nr channel matrices and each must represent L=25 rays.
    With Ne=119, Ns=50, Nr=10, we have 59500 matrices with 25 rays. It is better to save
    each episode in one file, with the matrix given by
    scene 1:Ns x Tx_index x Rx_index x numberRays and 7 numbers, the following for each ray
            path_gain
            timeOfArrival
            departure_elevation
            departure_azimuth
            arrival_elevation
            arrival_azimuth
            isLOS
    to simplify we assume that all episodes have the same number of scenes (e.g. 50) and receivers (e.g. 10).
    Episodes, scenes, etc, start counting from 0 (not 1).
    '''
    analysis_polygon = geometry.Polygon(
        [(c.analysis_area[0], c.analysis_area[1]),
        (c.analysis_area[2], c.analysis_area[1]),
        (c.analysis_area[2], c.analysis_area[3]),
        (c.analysis_area[0], c.analysis_area[3])])
    
    database_folder = c.result_dir_processed_data
    if not os.path.exists(database_folder):
        os.makedirs(database_folder)
    database_path = os.path.join(database_folder, f'{c.base_config.output_name}.db')

    numTxRxPairsPerScene = c.receivers_per_episode
    numVariablePerRay = 8 #has the ray phase now
    numRaysPerTxRxPair = 100

    if c.isolated_sim:
        numVariablePerRay = 8 #has the ray phase now
        session = fgdbIS.open_database(database_path)
    else:
        session = fgdb.open_database(database_path)
        totalNumEpisodes = session.query(fgdb.Episode).count()
        numScenesPerEpisode = c.scenes_per_episode
        
    # just to report time
    start = datetime.datetime.today()
    perc_done = None

    #Active if will restrict the analysis area
    Use_analysis_polygon = False
    #Generate npz file
    use_npz = False

    #if needed, manually create the output folder
    dataset_folder = os.path.join(database_folder, 'rays')
    if not os.path.exists(dataset_folder):
        os.makedirs(dataset_folder)
    fileNamePrefix = os.path.join(dataset_folder, 'rays_ep')
    pythonExtension = '.npz'
    matlabExtension = '.hdf5'

    numEpisode = 0
    numLOS = 0
    numNLOS = 0
    
    if c.isolated_sim:
        outputFileName = fileNamePrefix + str(numEpisode) + matlabExtension

        allEpisodeData = np.zeros((1, numTxRxPairsPerScene, numRaysPerTxRxPair,
                                numVariablePerRay), np.float32)
        allEpisodeData.fill(np.nan)

        for rec in session.query(fgdbIS.Receiver):
            
            ray_i = 0
            isLOSChannel = 0
            for ray in islice(rec.rays, numRaysPerTxRxPair): # Iterate over a minimum number of rays for each receiver
                #gather all info
                thisRayInfo = np.zeros(numVariablePerRay)
                thisRayInfo[0] = ray.path_gain
                thisRayInfo[1] = ray.time_of_arrival
                thisRayInfo[2] = ray.departure_elevation
                thisRayInfo[3] = ray.departure_azimuth
                thisRayInfo[4] = ray.arrival_elevation
                thisRayInfo[5] = ray.arrival_azimuth
                if ray.interactions_positions.count(',')>1:
                    thisRayInfo[6] = 1
                else:
                    thisRayInfo[6] = 0
                
                thisRayInfo[7] = ray.phase_in_degrees
                
                allEpisodeData[0][int(ray.receiver_id)-1][ray_i] = thisRayInfo
                ray_i += 1
                if thisRayInfo[6] == 1:
                    isLOSChannel = True #if one ray is LOS, the channel is
            if isLOSChannel == True:
                numLOS += 1
            else:
                numNLOS += 1
        outputFileName = fileNamePrefix +  str(numEpisode) + matlabExtension
        print('==> Wrote file ' + outputFileName)
        f = h5py.File(outputFileName, 'w')
        f['allEpisodeData'] = allEpisodeData
        f.close()
        
        del ray, rec, allEpisodeData
        gc.collect()

    else:
        for ep in session.query(fgdb.Episode): #go over all episodes
            outputFileName = fileNamePrefix + str(numEpisode) + matlabExtension
            #print('Processing ', ep.number_of_scenes, ' scenes in episode ', ep.insite_pah,)
            #print('Start time = ', ep.simulation_time_begin, ' and sampling period = ', ep.sampling_time, ' seconds')
            #print('Episode: ' + str(numEpisode) + ' out of ' + str(totalNumEpisodes))

            #initialization
            #Ns x [Tx_index x Rx_index x numberRays] and 7 numbers, the following for each ray
            allEpisodeData = np.zeros((numScenesPerEpisode, numTxRxPairsPerScene, numRaysPerTxRxPair,
                                    numVariablePerRay), np.float32)
            allEpisodeData.fill(np.nan)
            
            #from the first scene, get all receiver names
            rec_name_to_array_idx_map = [obj.name for obj in ep.scenes[0].objects if len(obj.receivers) > 0]
            # print(rec_name_to_array_idx_map)
            
            #process each scene in this episode
            #count # of ep.scenes
            for sc_i, sc in enumerate(ep.scenes):
                polygon_list = []
                polygon_z = []
                polygons_of_interest_idx_list = []
                rec_present = []
                
                for obj in sc.objects:
                    if len(obj.receivers) == 0:
                        continue  #do not process objects that are not receivers
                    obj_polygon = geometry.MultiPoint(obj.vertice_array[:,(0,1)]).convex_hull
                    # check if object is inside the analysis_area
                    if not Use_analysis_polygon:
                        # if the object is a receiver and is within the analysis area
                        if len(obj.receivers) > 0:
                            rec_array_idx = rec_name_to_array_idx_map.index(obj.name)
                            for rec in obj.receivers: #for all receivers
                                ray_i = 0
                                isLOSChannel = 0
                                for ray in rec.rays: #for all rays
                                    #gather all info
                                    thisRayInfo = np.zeros(numVariablePerRay)
                                    thisRayInfo[0] = ray.path_gain
                                    thisRayInfo[1] = ray.time_of_arrival
                                    thisRayInfo[2] = ray.departure_elevation
                                    thisRayInfo[3] = ray.departure_azimuth
                                    thisRayInfo[4] = ray.arrival_elevation
                                    thisRayInfo[5] = ray.arrival_azimuth
                                    thisRayInfo[6] = ray.is_los
                                    thisRayInfo[7] = ray.phaseInDegrees
                                    allEpisodeData[sc_i][rec_array_idx][ray_i]=thisRayInfo
                                    ray_i += 1
                                    if ray.is_los == 1:
                                        isLOSChannel = True #if one ray is LOS, the channel is
                                if isLOSChannel == True:
                                    numLOS += 1
                                else:
                                    numNLOS += 1
                                # just for reporting spent time
                    elif obj_polygon.within(analysis_polygon):
                        if len(obj.receivers) > 0:
                            rec_array_idx = rec_name_to_array_idx_map.index(obj.name)
                            for rec in obj.receivers: #for all receivers
                                ray_i = 0
                                isLOSChannel = 0
                                for ray in rec.rays: #for all rays
                                    #gather all info
                                    thisRayInfo = np.zeros(numVariablePerRay)
                                    thisRayInfo[0] = ray.path_gain
                                    thisRayInfo[1] = ray.time_of_arrival
                                    thisRayInfo[2] = ray.departure_elevation
                                    thisRayInfo[3] = ray.departure_azimuth
                                    thisRayInfo[4] = ray.arrival_elevation
                                    thisRayInfo[5] = ray.arrival_azimuth
                                    thisRayInfo[6] = ray.is_los
                                    thisRayInfo[7] = ray.phaseInDegrees
                                    allEpisodeData[sc_i][rec_array_idx][ray_i]=thisRayInfo
                                    ray_i += 1
                                    if ray.is_los == 1:
                                        isLOSChannel = True #if one ray is LOS, the channel is
                                if isLOSChannel == True:
                                    numLOS += 1
                                else:
                                    numNLOS += 1
                                # just for reporting spent time
                perc_done = ((sc_i + 1) / ep.number_of_scenes) * 100
                elapsed_time = datetime.datetime.today() - start
                time_p_perc = elapsed_time / perc_done
                #print('\r Done: {:.2f}% Scene: {} time per scene: {} time to finish: {}'.format(
                #    perc_done,
                #    sc_i + 1,
                #    elapsed_time / (sc_i + 1),
                #    time_p_perc * (100 - perc_done)), end='')

            if use_npz:
                print()
                outputFileName = fileNamePrefix +  str(numEpisode) + pythonExtension
                np.savez(outputFileName, allEpisodeData=allEpisodeData)
                print('==> Wrote file ' + outputFileName)

            outputFileName = fileNamePrefix +  str(numEpisode) + matlabExtension
            #print('==> Wrote file ' + outputFileName)
            f = h5py.File(outputFileName, 'w')
            f['allEpisodeData'] = allEpisodeData
            f.close()

            numEpisode += 1 #increment episode counter

            del ep, obj, ray, sc, rec, f, allEpisodeData, obj_polygon
            gc.collect()
