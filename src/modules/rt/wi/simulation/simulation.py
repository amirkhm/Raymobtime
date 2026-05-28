import os
import shutil
import numpy as np
import logging
import json
import traci
from src.scripts.helpers import format_run_name
from src.modules.rt.wi.modeling import  X3dXmlFile3_3
from src.modules.rt.wi.simulation.tools import *
from src.modules.rt.wi.modeling import (
    insite, 
    X3dXmlFile, 
    objects, 
    txrx)
from src.modules.rt.wi.simulation.placement import (
    place_on_line, 
    place_by_sumo)

def onlyDronesList(idList):
    for v_id, veh in enumerate(idList[:]):
        if not veh.startswith('dflow'):
            idList.remove(veh)
    return idList

def wireless_insite_simulation(c):
    if c.use_fixed_receivers and c.receivers_per_episode != 0:
        # At fixed receivers, position set on WI is maintained, 
        # that manner it should not change here, default zero.
        logging.error(f'if flag use_fixed_receivers=True, receivers_per_episode must be 0 but it is {c.receivers_per_episode}')
        raise Exception()
    if c.isolated_sim and c.use_vehicles_template:
        # isolated sim is intended to be static, no object is placed after modelling.
        logging.error('flags isolated_sim=True and use_vehicles_template=True are not compatible')
        raise Exception()

    insite_project = insite.InSiteProject(
        project_name='model', 
        calcprop_bin=c.calcprop_bin,
        wibatch_bin=c.wibatch_bin)

    logging.info('Simulation started')

    logging.debug('Simulation of ray-tracing will start. It is assumed all files have been placed')

    if c.isolated_sim:
        run_dir = os.path.join(c.isolated_results_dir)
        #Ray-tracing output folder (where InSite will store the results (Study Area name)).
        #They will be later copied to the corresponding output folder specified by results_dir
        project_output_dir = os.path.join(run_dir, c.insite_study_area_name) #output InSite folder

        p2mpaths_file = os.path.join(project_output_dir, c.insite_setup_name + '.paths.t001_01.r002.p2m')
        if not os.path.exists(p2mpaths_file) or c.base_config.clean_previous:
            xml_full_path = os.path.join(run_dir, c.dst_x3d_xml_file_name) #input InSite folder
            xml_full_path=xml_full_path.replace(' ', '\ ')
            insite_project.run_x3d(xml_full_path, project_output_dir)
        else: 
            raise Exception(f'{p2mpaths_file} already exists')
        return
    else:
        for i in c.n_run:
            run_dir = os.path.join(c.results_dir, format_run_name(i))
            #Ray-tracing output folder (where InSite will store the results (Study Area name)).
            #They will be later copied to the corresponding output folder specified by results_dir
            project_output_dir = os.path.join(run_dir, c.insite_study_area_name) #output InSite folder

            p2mpaths_file = os.path.join(project_output_dir, c.insite_setup_name + '.paths.t001_01.r002.p2m')
            if not os.path.exists(p2mpaths_file) or c.base_config.clean_previous:
                xml_full_path = os.path.join(run_dir, c.dst_x3d_xml_file_name) #input InSite folder
                xml_full_path=xml_full_path.replace(' ', '\ ')
                insite_project.run_x3d(xml_full_path, project_output_dir)
            elif os.path.exists(p2mpaths_file) and c.jump:
                continue
            else: 
                raise Exception(f'{p2mpaths_file} already exists')
            
    logging.info('Finished running ray-tracing')

def copytree_base_files(c):
    #copy files from initial (source folder) to results base folder
    try:
        shutil.copytree(c.base_insite_project_path, c.results_base_model_dir, )
    except FileExistsError:
        if c.base_config.clean_previous:
            shutil.rmtree(c.results_dir)
            print('Removed folder',c.results_dir)
            shutil.copytree(c.base_insite_project_path, c.results_base_model_dir, )
        else:
            print('### ERROR: folder / file exists:',c.results_base_model_dir)
            raise FileExistsError
    print('Copied folder ',c.base_insite_project_path,'into',c.results_base_model_dir)

def main(c):
    # if mobility enabled and check != ok execute
        # this make the positions
        # output them at file
    # if ray tracing enabled and check != ok execute
        # this copy the base files to the output folder
        # this take positions for parsing
        # this execute ray tracing



    if c.ray_tracing.enabled:
        wireless_insite_simulation(c)
        return
    
    
    copytree_base_files(c)
    
    #* Open files for parsing ============================================================
    #open InSite files that are used as the base to create each new scene / simulation
    with open(c.base_object_file_name) as infile:
        objFile = objects.ObjectFile.from_file(infile)
    print('Opened file with objects:', c.base_object_file_name)
    with open(c.base_txrx_file_name) as infile:
        txrxFile = txrx.TxRxFile.from_file(infile)
    print('Opened file with transmitters and receivers:', c.base_txrx_file_name)
    if c.insite_version == '3.3':
        x3d_xml_file = X3dXmlFile3_3(c.base_x3d_xml_path)
    else:
        x3d_xml_file = X3dXmlFile(c.base_x3d_xml_path)
    print('Opened file with InSite XML:', c.base_x3d_xml_path)
    #* End Open files for parsing ============================================================

    #* Create car structure for placement ====================================================
    car = objects.RectangularPrism(*c.car_dimensions, material=c.car_material_id)
    car_structure = objects.Structure(name=c.car_structure_name)
    car_structure.add_sub_structures(car)
    car_structure.dimensions = car.dimensions
    #* End Create car structure for placement ================================================

    antenna = txrxFile[c.antenna_points_name].location_list[0]

    if c.mobility.enabled and c.mobility.tool == 'line':
        count_nar = 0 # Number of Runs without cars with antenna while mobile
        for i in c.n_run:
            run_dir = os.path.join(
                c.results_dir, 
                format_run_name(i - count_nar))
            objFile.clear()
            structure_group, location = place_on_line(
                c.line_origin, 
                c.line_destination, 
                c.line_dimension,
                c.car_distances, 
                car_structure, 
                antenna, 
                c.antenna_origin)
    elif c.mobility.enabled and c.mobility.tool == 'sumo':
        np.random.seed(c.sumo.seed)
        logging.info('Starting SUMO')
        traci.start(c.sumo_cmd)

        scene_i = 0
        episode_i = 0

        # Jumps to the defined traci start
        for tmp_var in range(int(c.n_run[0])):
            # Only when switching episodes or for the first time choose vehicles to be receivers
            if scene_i == 0:
                while True:
                    # ensures number of receivers at beginning of episode
                    traci_vehicle_IDList = traci.vehicle.getIDList()
                    # Only drone, remove the non-drone vehicles from the list
                    if c.drone_simulation:
                        traci_vehicle_IDList = onlyDronesList(traci.vehicle.getIDList())
                    if len(traci_vehicle_IDList) < c.receivers_per_episode:
                        traci.simulationStep()
                        logging.debug(f'not enough vehicles at time {traci.simulation.getCurrentTime()}')
                    else:
                        break
                cars_with_antenna = np.random.choice(
                    traci_vehicle_IDList, 
                    c.receivers_per_episode, 
                    replace=False)
            else:
                # step at time scene or episode
                scene_i += 1
                if scene_i <= c.scenes_per_episode:
                    traci.simulationStep()
                else:
                    scene_i = 0
                    episode_i += 1
                    for _ in range(c.time_between_episodes):
                        traci.simulationStep()
            logging.info(f'Jump until the step {c.n_run[0]}: {int((tmp_var/c.n_run[0])* 100)}%')
    
    
        count_nar = 0 # Number of Runs without cars with antenna while mobile
        for i in c.n_run:
            run_dir = os.path.join(
                c.results_dir,
                format_run_name(i - count_nar))
            objFile.clear()

            if scene_i >= c.scenes_per_episode:
                # Step episode and reset scene
                episode_i += 1
                scene_i = 0
                # step time_between_episodes
                for count in range(c.time_between_episodes):
                    traci.simulationStep()
                if c.use_fixed_receivers:
                    cars_with_antenna = []
                    cars_with_Tx = None
                    antenna_Tx = None
                else:
                    # ensure that there enough cars to place antennas. 
                    # If use_fixed_receivers, then wait to have at least
                    # one vehicle
                    traci_vehicle_IDList = traci.vehicle.getIDList()
                    if c.drone_simulation: 
                        traci_vehicle_IDList = onlyDronesList(traci.vehicle.getIDList())
                    min_cars_per_episode = c.receivers_per_episode
                    if c.use_V2V:
                        # ensure that there enough cars to Rx and Tx antennas
                        min_cars_per_episode = (c.receivers_per_episode +c.n_Tx_per_episode)

                    while len(traci_vehicle_IDList) < min_cars_per_episode:
                        traci_vehicle_IDList = traci.vehicle.getIDList()
                        if c.drone_simulation: 
                            traci_vehicle_IDList = onlyDronesList(traci.vehicle.getIDList())
                        logging.warning(f'not enough vehicles at time {traci.simulation.getCurrentTime()}')
                        traci.simulationStep()

                    # chooses the cars with Rx antennas
                    cars_with_antenna = np.random.choice(traci_vehicle_IDList, c.receivers_per_episode, replace=False)
                    # Chose from the specific area
                    if c.set_area_limit:
                        def check_if_veh_in_area(veh_pos, min_lim, max_lim):
                            if veh_pos[0] < min_lim[0] or veh_pos[0] > max_lim[0]:
                                return False
                            if veh_pos[1] < min_lim[1] or veh_pos[1] > max_lim[1]:
                                return False
                            return True
                        
                        n_veh = 0

                        while n_veh < c.receivers_per_episode:
                            traci.simulationStep()
                            # Check if there is veh in the area, if not simulate an step and check again
                            traci_vehicle_IDList = traci.vehicle.getIDList()
                            veh_in_the_area, n_veh = pick_car_from_area(traci_vehicle_IDList, [c.min_lim, c.max_lim], c.receivers_per_episode, return_counts=True)
                        # Choose within the area
                        cars_with_antenna = np.random.choice(veh_in_the_area, c.receivers_per_episode, replace=False)

                    if c.use_V2V:
                        # chooses the cars with Tx antennas
                        traci_vehicle_IDList = traci.vehicle.getIDList()
                        if c.set_area_limit:
                            cars_with_Tx = pick_car_from_area(traci_vehicle_IDList, [c.min_lim, c.max_lim], c.n_Tx_per_episode)
                        else:
                            cars_with_Tx = np.random.choice(traci_vehicle_IDList, c.n_Tx_per_episode, replace=False)
                        traci_vehicle_IDList = [x for x in traci_vehicle_IDList if x not in cars_with_Tx]
                        if c.close_vehicles:
                            # Only works for 1 Tx
                            x, y = traci.vehicle.getPosition(cars_with_Tx[0])
                            pos_Tx = np.array(traci.simulation.convertGeo(x, y))

                            Rx_name = {}
                            all_distances = []
                            for veh in traci_vehicle_IDList:
                                x, y = traci.vehicle.getPosition(veh)
                                pos_Rx = np.array(traci.simulation.convertGeo(x, y))
                                dist = (np.sqrt(np.sum((pos_Tx-pos_Rx)**2)))
                                Rx_name[dist] = veh
                                all_distances.append(dist)
                            all_distances = np.sort(all_distances)[:c.n_of_vehicles]

                            traci_vehicle_IDList = [Rx_name[i] for i in all_distances]
                            cars_with_antenna = np.random.choice(traci_vehicle_IDList, c.receivers_per_episode, replace=False)

                        antenna_Tx = txrxFile[c.insite_tx_name].location_list[0]
                        # temp_cars = [x for x in traci_vehicle_IDList if x not in cars_with_antenna]
                        # cars_with_Tx = np.random.choice(temp_cars, c.n_Tx_per_episode, replace=False)
                        # antenna_Tx = txrxFile[c.insite_tx_name].location_list[0]
                    else:
                        cars_with_Tx = None
                        antenna_Tx = None
            else:
                traci.simulationStep()

            structure_group, location, location_Tx, str_vehicles = place_by_sumo(
                c,
                antenna,
                antenna_Tx,
                c.car_material_id,
                lane_boundary_dict=c.lane_boundary_dict,
                cars_with_antenna=cars_with_antenna,
                cars_with_Tx=cars_with_Tx,
                use_V2V=c.use_V2V,
                use_fixed_receivers = c.use_fixed_receivers,
                use_pedestrians = c.use_pedestrians)

            if c.use_sumo:
                # when to start a new episode
                if scene_i >= c.scenes_per_episode:
                    #first scene of an episode
                    if episode_i is None:
                        episode_i = 0
                    else:
                        episode_i += 1
                    scene_i = 0
                    # step time_between_episodes from the last one
                    
                else:
                    

                #if location is None:  #there are not cars with antennas in this episode (all have left)
                # no vehicles in the environment (not only the ones without antennas, but no vehicles at all)
                if traci.vehicle.getIDList() is None:
                    logging.warning("No vehicles in scene " + str(scene_i) + " time " + str(traci.simulation.getCurrentTime()))
                    os.makedirs(run_dir + '_novehicles') #create an empty folder to "indicate" the situation
                    #save SUMO information for this scene as text CSV file
                    sumoOutputInfoFileName = os.path.join(run_dir,'sumoOutputInfoFileName_novehicles.txt')
                    writeSUMOInfoIntoFile(sumoOutputInfoFileName, episode_i, scene_i, c.lane_boundary_dict, cars_with_antenna)
                    scene_i += 1 #update scene counter
                    continue

                # check if there are no cars with antenna in this episode (in this case all have left)
                if (location is None) or (location_Tx is None and c.use_V2V):
                    if not c.use_fixed_receivers:
                        count_nar = count_nar + 1
                        #abort, there is not reason to continue given that there will be no receivers along the whole episode
                        logging.warning("No vehicles with antennas in scene " + str(scene_i) + " time " + str(traci.simulation.getCurrentTime()))
                        os.makedirs(run_dir + '_noAntennaVehicles') #create an empty folder to "indicate" the situation
                        scene_i = np.Infinity #update scene counter
                        continue

            # Parsing =====================================================================================
            # Toda run limpa o objfile
            objFile.clear()

            # if use wireless insite copy base ============================================================
            shutil.copytree(c.base_insite_project_path, run_dir)
            print('Copied',c.base_insite_project_path,'into',run_dir)

            # writes at a run
            objFile.add_structure_groups(structure_group)
            dst_object_full_path = os.path.join(run_dir, c.dst_object_file_name)
            objFile.write(dst_object_full_path)

            #write new model of vehicles to the final folder
            if c.use_vehicles_template:
                dst_new_object_full_path = os.path.join(run_dir, c.insite_vehicles_name_model + '.object')
                f_dst_new_object = open(dst_new_object_full_path,'w')
                f_dst_new_object.write(str_vehicles)
                f_dst_new_object.close()

            #get name of XML
            xml_full_path = os.path.join(run_dir, c.dst_x3d_xml_file_name) #input InSite folder
            xml_full_path=xml_full_path.replace(' ', '\ ')

            if not c.use_fixed_receivers:
                x3d_xml_file.add_vertice_list(location, c.dst_x3d_txrx_xpath)
                if c.use_V2V:
                    x3d_xml_file.add_vertice_list(location_Tx, c.dst_x3d_txrx_xpath_to_tx)
                x3d_xml_file.write(xml_full_path)

                # add vertices from receivers to the txrx file
                txrxFile[c.antenna_points_name].location_list[0] = location
                if c.use_V2V:
                    txrxFile[c.insite_tx_name].location_list[0] = location_Tx # add vertices from transmitters to the txrx file
                # txrx modified in the RWI project
                dst_txrx_full_path = os.path.join(run_dir, c.dst_txrx_file_name)
                txrxFile.write(dst_txrx_full_path)

            with open(os.path.join(run_dir, c.simulation_info_file_name), 'w') as infofile:
                if c.use_V2V:
                    info_dict = dict(
                        cars_with_antenna=list(cars_with_antenna),
                        cars_with_Tx=list(cars_with_Tx),
                        scene_i=scene_i)
                else:
                    info_dict = dict(
                        cars_with_antenna=list(cars_with_antenna),
                        scene_i=scene_i)
                json.dump(info_dict, infofile)

            #save SUMO information for this scene as text CSV file
            sumoOutputInfoFileName = os.path.join(run_dir,'sumoOutputInfoFileName.txt')
            writeSUMOInfoIntoFile(
                sumoOutputInfoFileName, 
                episode_i, scene_i, 
                c.lane_boundary_dict, 
                cars_with_antenna, 
                cars_with_Tx, 
                c.use_fixed_receivers, 
                c.use_pedestrians)

            scene_i += 1 #update scene counter
        traci.close()

