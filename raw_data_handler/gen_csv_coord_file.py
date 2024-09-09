'''
Reads the database (e.g. episode.db) and then
generates a CSV with some basic information, which is later complemented
with ak_generateInSitePlusSumoList.py
Look at save5gmdata.py to understand the information stored in the database.
'''
import os
import csv
import numpy as np
from shapely import geometry
# from matplotlib import pyplot as plt
# import h5py

# from rwisimulation.positionmatrix import position_matrix_per_object_shape, calc_position_matrix
# from rwisimulation.calcrxpower import calc_rx_power

from raw_data_handler import save5gmdata as fgdb

# import config as c  #instead of reading from the config.py file, copy and paste here the used variables:
# class c:
#     analysis_area = (648, 348, 850, 685)
    # analysis_area = (-167,-120,136,144)
    # analysis_area = (744, 429, 767, 679)  # coordinates that define the areas the mobile objects should be
    # analysis_area_resolution = 0.5 #grid resolution in meters (not used here)
    # antenna_number = 4 #number of antenna elements in Rx array (not used here)
    # frequency = 6e10 #carrier frequency in Hz (not used here)


# construct an object to help identifying objects within the analysis area
# analysis_polygon = geometry.Polygon([(c.analysis_area[0], c.analysis_area[1]),
#                                      (c.analysis_area[2], c.analysis_area[1]),
#                                      (c.analysis_area[2], c.analysis_area[3]),
#                                      (c.analysis_area[0], c.analysis_area[3])])
def gen_csv_file(c):
    main_folder = os.path.join(c.working_directory, 'sim_data', c.sim_name)
    if not os.path.exists(main_folder):
        os.makedirs(main_folder)
    database_path = os.path.join(main_folder, f'{c.sim_name}.db')
    session = fgdb.open_database(database_path)
    
    analysis_polygon = geometry.Polygon([(c.analysis_area[0], c.analysis_area[1]),
                                     (c.analysis_area[2], c.analysis_area[1]),
                                     (c.analysis_area[2], c.analysis_area[3]),
                                     (c.analysis_area[0], c.analysis_area[3])])
    
    totalNumEpisodes = session.query(fgdb.Episode).count()

    numEpisode = 0
    numValidChannels = 0
    numInvalidChannels = 0
    numLOS = 0
    numNLOS = 0
    # Header
    
    coord_file_name = os.path.join(main_folder, 'CoordVehicleTxRx.csv')
    file = open(coord_file_name, 'w')
    file.writelines("Val,EpisodeID,SceneID,TxID,RxID,VehicleName,x,y,z,angles,rays,LOS\n")
    for ep in session.query(fgdb.Episode):  # go over all episodes
        # process each scene in this episode
        # count # of ep.scenes
        for sc_i, sc in enumerate(ep.scenes):
            # from the first scene, get all receiver names
            # this list is important because it allows to converts vehicle names to their indices. From a given episode,
            # a given vehicle name will always have the same index in this list
            rec_name_to_array_idx_map = [obj.name for obj in ep.scenes[0].objects if len(obj.receivers) > 0]
            tx_name_to_array_idx_map = [obj.name for obj in ep.scenes[0].objects if len(obj.transmitter) > 0]
            if False:
                print('The names of the mobile objects that have at a receiver in this episode are:')
                # See documentation at https://github.com/lasseufpa/5gm-rwi-simulation/wiki
                print(rec_name_to_array_idx_map)
            maxNumOfReceiversInThisEpisode = len(rec_name_to_array_idx_map)
            maxNumOfTransmittersInThisEpisode = len(tx_name_to_array_idx_map)

            # print('Processing scene # ', sc_i, ' with ID ', sc.id, ' from episode ', sc.episode_id,
            #      ' with ', sc.number_of_receivers, ' receivers and ', sc.number_of_mobile_objects, ' mobile objects')
            polygon_list = []
            polygon_z = []
            polygons_of_interest_idx_list = []
            rec_present = []

            # get data for all in this scene
            losReceiversInThisScene = np.zeros(maxNumOfReceiversInThisEpisode, dtype=bool)
            validReceiversInThisScene = np.zeros(maxNumOfReceiversInThisEpisode, dtype=bool)
            approximateReceiverPositions = np.zeros((maxNumOfReceiversInThisEpisode, 3))
            numOfRaysForThisReceiver = np.zeros(maxNumOfReceiversInThisEpisode, dtype=int)
            # 
            validTransmitterInThisScene = np.zeros(maxNumOfReceiversInThisEpisode, dtype=bool)
            approximateTransmitterPositions = np.zeros((maxNumOfReceiversInThisEpisode, 3))
            # sc.objects has sc.number_of_mobile_objects, which can be a large number (e.g. 53)
            for obj in sc.objects:  # get object in scene
                if len(obj.transmitter) > 0:
                    # if there is a transmitter, then it is V2v, and it does not have an analyses area
                    tx_array_idx = tx_name_to_array_idx_map.index(obj.name)
                    approximateTransmitterPositions[tx_array_idx] = obj.position
                    
                    if approximateTransmitterPositions[rec_array_idx, 0] == 0.0 and approximateTransmitterPositions[rec_array_idx, 1] == 0.0:
                        numInvalidChannels += 1
                        validTransmitterInThisScene[tx_array_idx] = False
                    else:
                        validTransmitterInThisScene[tx_array_idx] = True
                        numValidChannels += 1
                    
                if len(obj.receivers) == 0:
                    # print('Skipping ', obj.name, ' because it does not have a receiver!')
                    continue
                # only check if within area in case it's a receiver to avoid wasting time
                obj_polygon = geometry.MultiPoint(obj.vertice_array[:, (0, 1)]).convex_hull
                # check if object is inside the analysis_area
                rec_array_idx = rec_name_to_array_idx_map.index(obj.name)
                approximateReceiverPositions[rec_array_idx] = obj.position
                if (obj_polygon.within(analysis_polygon)) or (not c.analysis_area_enabled):
                    # print(obj.name, ' with ID ', obj.id, ' is within analysis area and has a receiver')
                    validReceiversInThisScene[rec_array_idx] = True
                    numValidChannels += 1
                else:
                    numInvalidChannels += 1
                    # print(obj.name, ' with ID ', obj.id, ' is not in analysis area')
                    continue
                    # if the object is a receiver and is within the analysis area
                    # in the 5gmv1 data this number is 0 or 1 (there is no more than 1 Rx per object)
                    # print(obj.name, ' has ', len(obj.receivers), ' receiver(s)')
                    # use the infamouse list to get the index corresponding to the mobile object with name obj.name
                # print(obj.name, ' is mapped to index ', rec_array_idx)
                if approximateReceiverPositions[rec_array_idx, 0] == 0.0 and approximateReceiverPositions[rec_array_idx, 1] == 0.0:
                    numInvalidChannels += 1
                    validReceiversInThisScene[rec_array_idx] = False

                if len(obj.receivers) > 1:
                    print('Was expecting only 1 receiver per vehicle')
                    exit(-1)
                for rec in obj.receivers:  # for all potential receivers
                    numOfRaysForThisReceiver[rec_array_idx] = len(rec.rays)
                    #print('aaaa',numOfRaysForThisReceiver[rec_array_idx])
                    for ray in rec.rays:  # for all rays
                        if ray.is_los == 1:
                            losReceiversInThisScene[rec_array_idx] = 1
                    # print('Scene ', sc_i, ', valids: ', validReceiversInThisScene)
                    if losReceiversInThisScene[rec_array_idx] == 1:
                        numLOS += 1
                    else:
                        numNLOS += 1
            # now have the info for all receivers. Print in order
            for i in range(maxNumOfReceiversInThisEpisode):
                
                thisString = str(numEpisode) + ',' + str(sc_i) + ',' + '-1' + ',' + str(i) + ',' + rec_name_to_array_idx_map[
                    i] + ',' + str(approximateReceiverPositions[i, 0]) + ',' + str(
                    approximateReceiverPositions[i, 1]) + ',' + str(numOfRaysForThisReceiver[i])
                if validReceiversInThisScene[i]:  # pre-append
                    thisString = 'V,' + thisString
                    if losReceiversInThisScene[i]:  # post-append
                        thisString = thisString + ',1'
                    else:
                        thisString = thisString + ',0'
                else:
                    thisString = 'I,' + thisString
                    thisString = thisString + ',-1'
                file.writelines(f'{thisString}\n')
            
            for i in range(maxNumOfTransmittersInThisEpisode):
                thisString = str(numEpisode) + ',' + str(sc_i) + ',' + str(i) + ',' + '-1' + ',' + tx_name_to_array_idx_map[i] + ',' + str(approximateReceiverPositions[i, 0]) + ',' + str(approximateReceiverPositions[i, 1]) + ',' + str(numOfRaysForThisReceiver[i])
                if validReceiversInThisScene[i]:  # pre-append
                    thisString = 'V,' + thisString
                else:
                    thisString = 'I,' + thisString
                thisString = thisString + ',-1'
                file.writelines(f'{thisString}\n')
                
        numEpisode += 1  # increment episode counter
    print('numValidChannels = ', numValidChannels)
    print('numInvalidChannels = ', numInvalidChannels)
    print('Sum = ', numInvalidChannels + numValidChannels)

    print('numLOS = ', numLOS)
    print('numNLOS = ', numNLOS)
    print('Sum = ', numNLOS + numLOS)
